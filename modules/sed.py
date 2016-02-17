from modules import Module
import re

class sed(Module):
	"""sed: implements sed's s// partially."""
	def start(self):
		self.buffer = {}
		self.buffer_max = 100
	
	def on_privmsg( self, source, target, message ):
		m = re.match( 's/(?P<from>[^/]+)/(?P<to>.*)/(?P<flags>g?)$', message )
		if not target in self.buffer:
			self.buffer[target] = []
		buff = self.buffer[target]
		if m:
			for item in buff:
				if item['message'] + '/' == message: # fix for me typing the damn command wrong
					continue
				if re.search( m.group('from'), item['message'] ):
					new_message = re.sub( m.group('from'), m.group('to'), item['message'] )
					self.privmsg( target, '<{0}> {1}'.format( item['source'], new_message ) )
					buff.insert( 0, { 'source': item['source'], 'target': item['target'], 'message': new_message } )
					break
		else:
			buff.insert( 0, { 'source': source, 'target': target, 'message': message } )
			if len( buff ) > self.buffer_max:
				buff.pop()
