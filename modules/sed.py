from _module import _module
import re

class sed( _module ):
	def __init__( self, config, bot ):
		super( sed, self ).__init__( config, bot )
		self.buffer = []
		self.buffer_max = 100
	
	def on_privmsg( self, source, target, message ):
		m = re.match( 's/(?P<from>[^/]+)/(?P<to>.*)/$', message )
		if m:
			for item in self.buffer:
				if re.search( m.group('from'), item['message'] ):
					new_message = re.sub( m.group('from'), m.group('to'), item['message'] )
					bot.privmsg( target, '<{0}> {1}'.format( item['source'], new_message ) )
					self.buffer.insert( 0, { 'source': item['source'], 'target': item['target'], 'message': new_message } )
					break
		else:
			self.buffer.insert( 0, { 'source': source, 'target': target, 'message': message } )
			if len( self.buffer ) > self.buffer_max:
				self.buffer.pop()
