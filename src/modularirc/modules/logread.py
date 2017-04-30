import os
import shlex
import argparse

import datetime
from collections import OrderedDict

from modularirc import BaseModule


class ZncLogReader:
    OLD_PATH_FMT = '{}_{}_{:%Y%m%d}.log'
    NEW_PATH_FMT = '{}/{}/{:%Y-%m-%d}.log'

    def __init__(self, path):
        self.log_dir = path

    def get_all_logs(self):
        networks = OrderedDict()
        for filename in sorted(os.listdir(self.log_dir)):
            fullname = os.path.join(self.log_dir, filename)
            if os.path.isdir(fullname):
                network = filename
                if not network in networks:
                    networks[network] = OrderedDict()
                for windowname in sorted(os.listdir(fullname)):
                    window = windowname
                    if not window in networks[network]:
                        networks[network][window] = []
                    for datefile in sorted(os.listdir(os.path.join(fullname, window))):
                        try:
                            date = datetime.datetime.strptime(datefile, '%Y-%m-%d.log').date()
                            networks[network][window].append(date)
                        except ValueError:
                            continue

        return networks

    def get_networks(self):
        logs = self.get_all_logs()
        return sorted(logs.keys())

    def get_windows(self, network):
        logs = self.get_all_logs()
        if network in logs:
            return sorted(logs[network].keys())
        return []

    def get_logs(self, network, window):
        logs = self.get_all_logs()
        if network in logs:
            if window in logs[network]:
                return sorted(logs[network][window])
        return []

    def get_log_file(self, network, window, date):
        old_style = os.path.join(self.log_dir, ZncLogReader.OLD_PATH_FMT.format(network, window, date))
        new_style = os.path.join(self.log_dir, ZncLogReader.NEW_PATH_FMT.format(network, window, date))

        have_old = os.path.exists(old_style)
        have_new = os.path.exists(new_style)

        filename = None
        if have_new:
            filename = new_style
        elif have_old:
            filename = old_style

        if filename is not None:
            return [line.strip() for line in open(filename, 'r', encoding='latin-1').readlines()]
        else:
            logging.warning('wtf no file')
        return []

    def search_log(self, network, window, query, argv):
        max_count = argv.line_count
        logs = self.get_all_logs()
        if not network in logs:
            return
        if not window in logs[network]:
            return
        for log_date in reversed(logs[network][window]):
            for line in reversed(self.get_log_file(network, window, log_date)):
                try:
                    msg_time, msg_sender, msg = line.split(None, 2)
                except ValueError:
                    continue
                msg_time = datetime.datetime.strptime(msg_time, '[%H:%M:%S]').time()
                msg_datetime = datetime.datetime.combine(log_date, msg_time)
                if not argv.search_commands and msg[0] == '!':
                    continue
                if argv.nickname:
                    if not msg_sender[1:-1].lower() == argv.nickname.lower():
                        continue
                if argv.case_insensitive:
                    has = query in line.lower()
                else:
                    has = query in line
                if has:
                    yield msg_datetime, msg_sender, msg
                    max_count -= 1
                    if max_count == 0:
                        return


class Module(BaseModule):
    logfile = os.path.join(os.path.dirname(__file__), '..', 'ircbot.log')

    def start(self):
        try:
            self.log_path = self.get_config('log_path')
            self.network = self.get_config('network')
            self.window = self.get_config('window')
        except:
            self.log_path = None
            self.network = None
            self.window = None

    def admin_cmd_search_log(self, raw_args, **kwargs):
        if not self.log_path:
            yield 'Module not configured correctly.'
            return
        argv = shlex.split(raw_args)
        parser = argparse.ArgumentParser()
        parser.add_argument('-i', action='store_true', dest='case_insensitive')
        parser.add_argument('-C', action='store_true', dest='search_commands')
        parser.add_argument('-c', type=int, default=1, dest='line_count')
        parser.add_argument('-n', '--nickname', dest='nickname')
        parser.add_argument('query', nargs='*')
        try:
            argv = parser.parse_args(argv)
        except SystemExit:
            yield 'Error parsing arguments'
            return

        query = ' '.join(argv.query)
        if argv.case_insensitive:
            query = query.lower()

        log_reader = ZncLogReader(self.log_path)
        result = log_reader.search_log(self.network, self.window, query, argv)
        for date, sender, msg in result:
            yield '[{}] {} {}'.format(date, sender, msg)

    def admin_cmd_logread(self, arglist, **kwargs):
        return self.read_log(*arglist)

    def read_log(self, count=10):
        try:
            count = int(count)
        except ValueError:
            return ['Invalid count']
        try:
            with open(self.logfile, 'rt') as f:
                log = f.readlines()
        except IOError:
            return ['Unable to read logfile.']
        return log[len(log)-count:]