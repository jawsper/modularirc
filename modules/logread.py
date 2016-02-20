from modules import Module
import os

class logread(Module):
    logfile = os.path.join(os.path.dirname(__file__), '..', 'ircbot.log')
    
    def admin_cmd_logread(self, arglist, **kwargs):
        return self.read_log(*arglist)

    def read_log(self, count=10):
        try:
            count = int(count)
        except ValueError:
            return ['Invalid count.']
        try:
            with open(self.logfile, 'rt') as f:
                log = f.readlines()
        except IOError:
            return ['Unable to read logfile.']
        return log[len(log)-count:]