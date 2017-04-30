import json

from modularirc import BaseModule


class Module(BaseModule):
    """event: Create and join an event."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.event = Event()

        try:
            self.event.load(self.get_config('event'))
        except Exception as e:
            pass

    def __del__(self):
        self.set_config('event', self.event.dump())

    def cmd_event(self, **kwargs):
        """!event: view current event"""
        if self.event.name:
            return ['Current event is called "{}", {} participant(s).'.format(self.event.name, len(self.event.participants))]
        else:
            return ['Currently there is no event.']

    def cmd_event_who(self, **kwargs):
        """!event_who: see who are in event"""
        if not self.event.name:
            return ['Currently there is no event.']
        else:
            if len(self.event.participants) > 0:
                return ['Participants ({}): {}'.format(len(self.event.participants), ', '.join(self.event.participants))]
            else:
                return ['No-one is currently participating.']

    def cmd_event_set(self, args, **kwargs):
        """!event_set: set or clear event name"""
        self.event.name = ' '.join(args)
        if not self.event.name:
            return ['Event disabled.']
        return ['Event name is now: "{}".'.format(self.event.name)]

    def cmd_event_reset(self, **kwargs):
        """!event_reset: clear event"""
        if not self.event.name:
            return ['No event currently.']
        self.event.name = ''
        self.event.participants = []
        return ['Event cleared.']

    def cmd_join(self, arglist, source, **kwargs):
        """!join: join current event"""
        if not self.event.name:
            return ['No event currently']

        if len(arglist) > 0:
            name = arglist[0]
            if self.event.join(name):
                return ['Thank you for adding "{}".'.format(name)]
            else:
                return ['"{}" is already participating.'.format(name)]
        else:
            if self.event.join(source):
                return ['Thank you for joining.']
            else:
                return ['You are already participating.']

    def cmd_leave(self, arglist, source, **kwargs):
        """!leave: leave current event"""
        if not self.event.name:
            return ['No event currently']

        if len(arglist) > 0:
            name = arglist[0]
            if self.event.leave(name):
                return ['Thank you for removing "{}".'.format(name)]
            else:
                return ['"{}" is not participating.'.format(name)]
        else:
            if self.event.leave(source):
                return ['Thank you for leaving.']
            else:
                return ['You are not participating.']

class Event:
    def __init__(self):
        self.name = ''
        self.participants = []

    def load(self, raw):
        try:
            data = json.loads(raw)
            self.name = data['name']
            self.participants = data['participants']
        except Exception as e:
            pass

    def dump(self):
        return json.dumps(dict(name=self.name, participants=self.participants))

    def join(self, name):
        if not name in self.participants:
            self.participants.append(name)
            return True
        return False

    def leave(self, name):
        if name in self.participants:
            self.participants.remove(name)
            return True
        return False
