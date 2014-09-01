from ._module import _module
import logging
import json

class reminder( _module ):
    def __init__(self, mgr):
        _module.__init__(self, mgr)
        try:
            self.reminders = json.loads(self.get_config('reminders'))
        except:
            self.reminders = {}
    def __del__(self):
        self.set_config('reminders', json.dumps(self.reminders))

    def on_join(self, c, e):
        name = e.source.nick
        if name is not c.get_nickname():
            logging.debug('%s joined %s', name, e.target)
            if name in self.reminders:
                for reminder_source, reminder_message in self.reminders[name].items():
                    self.notice(e.target, 'Welcome {}, <{}> wanted you to know this: {}'.format(name, reminder_source, reminder_message))
                del self.reminders[name]

    def cmd_reminder(self, args, source, target, admin):
        """!reminder <name> [<message>]: send <name> a message when they join, if message is empty then reminder will be cleared."""
        if len(args) < 1:
            return [self.cmd_reminder.__doc__]
        name = args[0]
        message = ' '.join(args[1:])
        for channel_name, channel in self.mgr.bot.channels.items():
            if channel.has_user(name):
                return ['User {} is already present'.format(name)]

        if name in self.reminders:
            if source in self.reminders[name]:
                if len(message) == 0:
                    del self.reminders[name][source]
                    return ['Reminder cleared']
                else:
                    self.reminders[name][source] = message
                    return ['New reminder set']
            else:
                if len(message) == 0:
                    return ['No reminder to be cleared']
                else:
                    self.reminders[name][source] = message
                    return ['Reminder set']
        else:
            if len(message) == 0:
                return ['No reminder to be cleared']
            else:
                self.reminders[name] = {}
                self.reminders[name][source] = message
                return ['Reminder set']