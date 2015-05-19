from modules import Module
import ubusrpc
import json

class who(Module):
	"""who: see who's here"""
	def __init__(self, mgr):
		super().__init__(mgr)

		config = {}
		try:
			config['hosts'] = json.loads(self.get_config('hosts'))
		except Exception as e:
			config['hosts'] = []

		self.ubus_rpc = ubusrpc.Main(config)

	def admin_cmd_who_reconfigure(self, **kwargs):
		config = {}
		try:
			config['hosts'] = json.loads(self.get_config('hosts'))
		except Exception as e:
			config['hosts'] = []

		self.ubus_rpc = ubusrpc.Main(config)

	def cmd_who(self, **kwargs):
		"""!who: see who's here"""
		self.ubus_rpc.update()
		if len(self.ubus_rpc.clients) == 0:
			return ['No-one is on the wifi.']
		else:
			return ['{} wifi client(s) online currently.'.format(len(self.ubus_rpc.clients))]
