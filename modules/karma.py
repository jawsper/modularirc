from _module import _module

class karma( _module ):
	def __init__( self, config, bot ):
		super( karma, self ).__init__( config, bot )
		self.karma = {}
	def on_privmsg( self, bot, source, target, message ):
		if message[-2:] == '++' or message[-2:] == '--':
			item = message[ :-2 ]
			if ' ' in item: # no spaces
				return
			scoring = 1 if message[-2:] == '++' else -1
			if not item in self.karma:
				self.karma[ item ] = 0
			self.karma[ item ] += scoring
			reply = '\x02{0}\x0F gave \x02{1}\x0F some sweet karma (now at {2})' if scoring > 0 else '\x02{0}\x0F dislikes \x02{1}\x0F, and removed karma (now at {2})'
			bot.notice( target, reply.format( source, item, self.karma[ item ] ) )
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
			] + map( lambda ( item, karma ): ' * {0}: {1}'.format( item, karma ), self.karma.iteritems() )
			