import json

from modularirc import BaseModule


class Module(BaseModule):
    """karma: give or take karma. karma is given with !<something><operator> # <reason>. <operator> is ++ or --, reason is optional """
    def start(self):
        try:
            self.karma = json.loads(self.get_config('karma'))
        except:
            self.karma = []

    def stop(self):
        self.set_config('karma', json.dumps(self.karma))
    
    def on_privmsg( self, source, target, message ):
        
        # require starting !
        if message[0] != '!':
            return
        # strip it off
        message = message[1:]
        
        # find comment
        comment = None
        if '#' in message:
            comment = message[ message.find( '#' ) + 1 : ].strip()
            message = message[ : message.find( '#' ) ].strip()
        
        if message[-2:] == '++' or message[-2:] == '--':
            item = message[ :-2 ]
            scoring = 1 if message[-2:] == '++' else -1
            self.karma.append( { 'item': item, 'mutation': scoring, 'source': source, 'comment': comment } )
            reply = '\x02{0}\x0F gave "{1}" some sweet karma (now at {2})' if scoring > 0 else '\x02{0}\x0F dislikes "{1}", and removed karma (now at {2})'
            self.notice( target, reply.format( source, item, self.item_karma( item ) ) )
    
    def item_karma_list( self, item ):
        return [ v for v in self.karma if v['item'] == item ]
    
    def item_karma( self, item ):
        karma = 0
        for evt in [ v for v in self.karma if v['item'] == item ]:
            karma += evt['mutation']
        return karma
    
    def total_karma( self ):
        items = {}
        for evt in self.karma:
            item = evt['item']
            if not item in items:
                items[ item ] = 0
            items[ item ] += evt['mutation']
        return items
    
    def cmd_karma(self, **kwargs):
        """!karma: shows all karma"""
        if len( self.karma ) == 0:
            return [ 'No karma given out yet. (Maybe you should!)' ]
        return [
            'Karma: {}'.format('; '.join(['{}: {}'.format(*item_karma) for item_karma in self.total_karma().items()]))
        ]

    def cmd_karmawhy(self, arglist,  **kwargs):
        """!karmawhy [<what>]: show last karma, optionally for item name"""
        if len( self.karma ) == 0:
            return [ 'No karma given out yet. (Maybe you should!)' ]
        karma_format = '{source} gave "{item}" {mutation} because "{comment}"'
        if len( arglist ) == 0:
            return [ 'Last karma: ', karma_format.format( **self.karma[ -1 ] ) ]
        elif len( arglist ) == 1:
            item = arglist[0]
            karma = self.item_karma_list( item )
            if len( karma ) == 0:
                return [ 'Karma has not been applied to "{0}"'.format( item ) ]
            return [ 'Last karma for "{0}":'.format( item ), karma_format.format( **karma[ -1 ] ) ]
