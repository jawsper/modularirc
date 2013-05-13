from _module import _module
import re

class sed( _module ):
	def __init__( self, config, bot ):
		super( sed, self ).__init__( config, bot )
		self.buffer = []
	
	def on_privmsg( self, bot, source, target, message ):
		m = re.match( 's/(?P<from>[^/]+)/(?P<to>.*)$', message )
		if m:
			for item in self.buffer:
				if re.search( m.group('from'), item['message'] ):
					bot.notice( target, '<{0}> {1}'.format( item['source'], re.sub( m.group('from'), m.group('to'), item['message'] ) ) )
		else:
			self.buffer.append( { 'source': source, 'target': target, 'message': message } )
			if len( self.buffer ) > 10:
				self.buffer = self.buffer[ 1: ]