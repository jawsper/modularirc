from _module import _module

class karma( _module ):
	def __init__( self, config, bot ):
		super( karma, self ).__init__( config, bot )
		self.karma = {}
	def on_privmsg( self, bot, source, target, message ):
		if message[-2:] == '++' or message[-2:] == '--':
			item = message[ :-2 ]
			scoring = 1 if message[-2:] == '++' else -1
			if not item in self.karma:
				self.karma[ item ] = 0
			self.karma[ item ] += scoring
			bot.notice( source, '{0}: {1}'.format( item, self.karma[ item ] ) )