import logging
import json

from datetime import datetime
from dateutil.tz import tzlocal

from modularirc import BaseModule


class Module(BaseModule):
    def start(self):
        try:
            self.reminders = json.loads(self.get_config('reminders'))
        except:
            self.reminders = {}
    def __del__(self):
        self.set_config('reminders', json.dumps(self.reminders))

    def on_join(self, connection, event):
        name = event.source.nick
        if name is not connection.get_nickname():
            name = name.lower()
            logging.debug('%s joined %s', name, event.target)
            if name in self.reminders:
                for sender, reminder in self.reminders[name].items():
                    self.notice(event.target, 'Welcome {}, <{}> said this at {date} for you: {message}'.format(event.source.nick, sender, **reminder))
                del self.reminders[name]

    def cmd_reminder(self, args, source, **kwargs):
        """!reminder <name> [<message>]: send <name> a message when they join, if message is empty then reminder will be cleared."""
        if len(args) < 1:
            return [self.cmd_reminder.__doc__]
        name = args[0].lower()
        message = ' '.join(args[1:])
        for channel_name, channel in self.mgr.bot.channels.items():
            if channel.has_user(name):
                return ['User {} is already present'.format(name)]

        date = datetime.now(tzlocal()).strftime('%Y-%m-%d %H:%M:%S%z')
        reminder = {'date': date, 'message': message}

        if name in self.reminders:
            if source in self.reminders[name]:
                if len(message) == 0:
                    del self.reminders[name][source]
                    return ['Reminder cleared']
                else:
                    self.reminders[name][source] = reminder
                    return ['New reminder set']
            else:
                if len(message) == 0:
                    return ['No reminder to be cleared']
                else:
                    self.reminders[name][source] = reminder
                    return ['Reminder set']
        else:
            if len(message) == 0:
                return ['No reminder to be cleared']
            else:
                self.reminders[name] = {}
                self.reminders[name][source] = reminder
                return ['Reminder set']