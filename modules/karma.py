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
			reply = '\x02{0}\x0F gave "{1}" some sweet karma (now at {2})' if scoring > 0 else '\x02{0}\x0F dislikes "{1}", and removed karma (now at {2})'
			bot.notice( target, reply.format( source, item, self.item_karma( item ) ) )
	
	def item_karma_list( self, item ):
		return filter( lambda v: v['item'] == item, self.karma )
	
	def item_karma( self, item ):
		karma = 0
		for evt in filter( lambda v: v['item'] == item, self.karma ):
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
	
	def can_handle( self, cmd, admin ):
		return cmd in ( 'karma', 'karmawhy' )
	
	def handle( self, bot, cmd, args, source, target, admin ):
		if cmd == 'help':
			return [ '!karma: shows all karma', '!karmawhy [<what>]: show last karma, optionally for item name' ]
		elif cmd == 'karma':
			if len( self.karma ) == 0:
				return [ 'No karma given out yet. (Maybe you should!)' ]
			return [
				'Karma:'
			] + map( lambda ( item, karma ): ' * {0}: {1}'.format( item, karma ), self.total_karma().iteritems() )
		elif cmd == 'karmawhy':
			if len( self.karma ) == 0:
				return
			karma_format = '{source} gave "{item}" {mutation} because "{comment}"'
			if len( args ) == 0:
				return [ 'Last karma: ', karma_format.format( **self.karma[ -1 ] ) ]
			elif len( args ) == 1:
				item = args[0]
				karma = self.item_karma_list( item )
				if len( karma ) == 0:
					return [ 'Karma has not been applied to "{0}"'.format( item ) ]
				return [ 'Last karma for "{0}":'.format( item ), karma_format.format( **karma[ -1 ] ) ]
			