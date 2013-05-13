from _module import _module

class karma( _module ):
	def __init__( self, config, bot ):
		super( karma, self ).__init__( config, bot )
		self.karma = []
	
	def on_privmsg( self, bot, source, target, message ):
		
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
			reply = '\x02{0}\x0F gave \x02{1}\x0F some sweet karma' if scoring > 0 else '\x02{0}\x0F dislikes \x02{1}\x0F, and removed karma'
			bot.notice( target, reply.format( source, item ) )
		
	def total_karma( self ):
		items = {}
		for evt in self.karma:
			item = evt['item']
			if not item in items:
				items[ item ] = 0
			items[ item ] += evt['mutation']
		return items
	
	def can_handle( self, cmd, admin ):
		return cmd in ( 'karma', )
	
	def handle( self, bot, cmd, args, source, target, admin ):
		if cmd == 'help':
			return [ '!karma: shows all karma' ]
		elif cmd == 'karma':
			if len( self.karma ) == 0:
				return [ 'No karma given out yet. (Maybe you should!)' ]
			return [
				'Karma:'
			] + map( lambda ( item, karma ): ' * {0}: {1}'.format( item, karma ), self.total_karma().iteritems() )
			
			