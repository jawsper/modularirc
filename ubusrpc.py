import json
import urllib.request
from datetime import datetime, timedelta
import os
import re
from collections import OrderedDict
import time

class JSONRPCException(Exception):
    def __init__(self, rpcError):
        Exception.__init__(self)
        self.error = rpcError

class LoginError(Exception):
    def __init__(self, error):
        self.error = error
    def __str__(self):
        return 'LoginError: {}'.format(self.error)

class UbusRPC:
    session_id = '00000000000000000000000000000000'

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        # self.login()

    def login(self):
        result_code, result = self.call('session', 'login', {'username': self.username, 'password': self.password})

        # print(result)
        if 'ubus_rpc_session' in result:
            self.session_id = result['ubus_rpc_session']
        else:
            raise LoginError(result)
    def call(self, *args):
        try:
            return self.post('call', self.session_id, *args)
        except JSONRPCException as e:
            if 'code' in e.error and e.error['code'] == -32002:
                # login failed
                try:
                    self.login()
                    return self.post('call', self.session_id, *args)
                except JSONRPCException as e:
                    print(e)
            else:
                print(e.error)
        return -1, None

    def post(self, method, *args):
        postdata = json.dumps({"method": method, 'params': args, 'id':'1', 'jsonrpc': '2.0'}).encode('utf-8')
        respdata = urllib.request.urlopen(self.url, postdata).read()
        resp = json.loads(respdata.decode('utf-8'))
        if 'error' in resp and resp['error'] != None:
            raise JSONRPCException(resp['error'])
        else:
            return resp['result']



class MACDatabase(OrderedDict):
    WIRESHARK_DB_PATH = '/usr/share/wireshark/manuf'
    WIRESHARK_DB_URL = 'https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf'
    def __init__(self):
        super().__init__()
        self.update(self.parse_wireshark_db())

    def mac_name(self, mac):
        if mac[:8] in self:
            name = '{} ({})'.format(mac, self[mac[:8]])
        else:
            name = mac
        return name

    def parse_wireshark_db(self):
        if os.path.isfile(self.WIRESHARK_DB_PATH):
            filename = self.WIRESHARK_DB_PATH
        else:
            filename = 'manuf'
            if not os.path.isfile(filename):
                with open(filename, 'wb') as f:
                    f.write(urllib.request.urlopen(self.WIRESHARK_DB_URL).read())
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                if line[0] == '#':
                    continue
                mac, name = line.split('\t', 1)

                # ignore these for now
                if not ':' in mac:
                    continue
                # also these complicated ones
                if len(mac) > 8:
                    continue

                mac = mac.lower()
                name_list = list(map(lambda x: x.strip(), name.split('#', 1)))
                if len(name_list) > 1:
                    name = name_list[1]
                yield mac, name

class DHCPLease(dict):
    def __init__(self, params):
        self.update(params)
    def __str__(self):
        start = self['expiry'] - timedelta(hours=12)
        return '{ip} {name} {0}'.format(start, **self)

    @staticmethod
    def parse_dhcp_leases(data):
        # timestamp mac ip name client_id
        for line in data.split('\n'):
            if len(line.strip()) == 0:
                continue
            expiry, mac, ip, name, client_id = line.split(' ')
            expiry = datetime.fromtimestamp(int(expiry))
            yield mac.lower(), DHCPLease({'mac': mac.lower(), 'ip': ip, 'name': name, 'expiry': expiry, 'client_id': client_id})

class WifiClient:
    def __init__(self, device, data):
        self.device = device
        self.mac = data['mac'].lower()
        self.data = []
        self.data.append(data)
    def append(self, data2):
        self.data.append(data2)

    def __eq__(self, other):
        if hasattr(other, 'device') and hasattr(other, 'mac'):
            return self.device == other.device and self.mac == other.mac
        else:
            return self.mac == other
    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return 'WifiClient({})'.format(self.mac)
    def __repr__(self):
        return 'WifiClient({})'.format(self.mac)

class UbusHost:
    def __init__(self, hostname, username, password):
        self.devices = OrderedDict()
        self.rpc = UbusRPC(hostname, username, password)
        self.load_devices()

    def load_devices(self):
        result = self.rpc.call('iwinfo', 'devices', {})
        if result[0] == 0:
            for device in sorted(result[1]['devices']):
                result = self.rpc.call('iwinfo', 'info', {'device': device})
                if result[0] == 0:
                    self.devices[device] = result[1]

    def get_assoclist(self):
        assoclist = OrderedDict()
        for device in self.devices.keys():
            result = self.rpc.call('iwinfo', 'assoclist', {'device': device})
            if result[0] == 0:
                assoclist[device] = map(lambda c: WifiClient(device, c), result[1]['results'])
        return assoclist

    def get_dhcp_leases(self):
        result = self.rpc.call('file', 'read', {'path': '/tmp/dhcp.leases'})
        if result[0] == 0:
            return DHCPLease.parse_dhcp_leases(result[1]['data'])
        return []

class Main:
    def __init__(self, cfg):
        self.ubus_hosts = []
        self.mac_db = MACDatabase()
        self.cfg = cfg
        for host in cfg['hosts']:
            self.client_add(host)

    def client_add(self, ubus):
        u = UbusHost('http://{}/ubus'.format(ubus['hostname']), ubus['username'], ubus['password'])
        self.ubus_hosts.append(u)

    def update(self):
        self.clients = []
        self.dhcp = {}
        for ubus in self.ubus_hosts:
            for device, clients in ubus.get_assoclist().items():
                self.clients.extend(clients)
            self.dhcp.update(ubus.get_dhcp_leases())

    def output(self):
        if len(self.clients) > 0:
            for client in self.clients:
                mac_name = self.mac_db.mac_name(client.mac)
                if client.mac in self.dhcp:
                    print('WIFI:', mac_name, self.dhcp[client.mac])
                else:
                    print('WIFI:', mac_name)
        else:
            print('No wifi clients')
        for mac, lease in self.dhcp.items():
            if mac in self.clients:
                continue
            print('DHCP:', mac, lease)


def test():
    c1 = WifiClient("device", {'mac': "testmac"})
    c2 = WifiClient("device", {'mac': "testmac2"})
    c3 = [c1, c2]
    print(c1 == c2)
    print(c1 == "testmac")
    print('testmac' in c3)

if __name__ == '__main__':
    # test()
    with open(os.path.expanduser('~/.config/ubusrpc.json'), 'r') as f:
        config = json.load(f)
    m = Main(config)
    while True:
        m.update()
        m.output()
        time.sleep(5)
        print('-'*30)
