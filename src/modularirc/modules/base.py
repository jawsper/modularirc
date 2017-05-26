import logging

class BaseModule(object):
    def __init__(self, manager, has_commands=True, admin_only=False):
        self.bot = manager.bot
        self.has_commands = has_commands
        self.admin_only = admin_only
        logging.info('Module {0} __init__'.format(self.__module__.split('.')[-1]))
        self.start()

    def __del__(self):
        logging.info('Module {0} __del__'.format(self.__module__.split('.')[-1]))
        self.stop()

    def enable(self):
        self.start()

    def disable(self):
        self.stop()

    def start(self):
        pass

    def stop(self):
        pass

    def get_cmd_list(self, prefix='cmd_'):
        return ['!{0}'.format(cmd[len(prefix):]) for cmd in dir(self) if cmd.startswith(prefix)]

    def has_cmd(self, cmd, prefix='cmd_'):
        return hasattr(self, '{}{}'.format(prefix, cmd))

    def get_cmd(self, cmd, prefix='cmd_'):
        return getattr(self, '{}{}'.format(prefix, cmd))

    def get_admin_cmd_list(self):
        return self.get_cmd_list(prefix='admin_cmd_')

    def has_admin_cmd(self, cmd):
        return self.has_cmd(cmd, prefix='admin_cmd_')

    def get_admin_cmd(self, cmd):
        return self.get_cmd(cmd, prefix='admin_cmd_')

    # methods that directly call the bot

    def notice(self, target, message):
        self.bot.notice(target, message)

    def privmsg(self, target, message):
        self.bot.privmsg(target, message)

    def get_config(self, key, default=None):
        return self.bot.get_config(self.__class__.__name__, key, default)

    def set_config(self, key, value):
        self.bot.set_config(self.__class__.__name__, key, value)

    def get_module(self, name):
        return self.bot.get_module(name)
