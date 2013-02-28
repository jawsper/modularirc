from __future__ import print_function
import os, json, pickle, re
import httplib, urllib
from _module import _module

class google( _module ):
	"""Bot module to search on google"""
	google_cache_file = os.path.expanduser( '~/.google_cache' )
	
	def __init__( self, config, bot ):
		_module.__init__( self, config, bot )

		if not os.path.exists( self.google_cache_file ):
			with open( self.google_cache_file, 'w' ):
				pass
		with open( self.google_cache_file, 'rb' ) as f:
			try:
				self.google_cache = pickle.load( f )
			except EOFError:
				self.google_cache = {}
				
	def can_handle( self, cmd, admin ):
		return self.api_key and self.cx and cmd == 'google' or ( admin and cmd == 'google_clear_cache' )
		
	def handle( self, bot, cmd, args, source, target, admin ):
		if admin and cmd == 'google_clear_cache':
			self.google_cache = {}
		if cmd == 'google':
			query = ' '.join( args )
		
			if not query in self.google_cache:
				conn = httplib.HTTPSConnection( 'www.googleapis.com' )
				conn.request(
					'GET',
					'/customsearch/v1?' + urllib.urlencode({
						'cx': self.cx,
						'key': self.api_key,
						'q': query
					})
				)
				response = conn.getresponse()
			
				self.google_cache[ query ] = json.load( response )
				with open( self.google_cache_file, 'wb' ) as f:
					pickle.dump( self.google_cache, f )
			
			results = self.google_cache[ query ]
			if 'items' in results and results['items'] and results['items'][0]:
				return [
					"{0}: {1}".format(
						results['items'][0]['title'].encode('ascii', 'ignore'),
						results['items'][0]['link']
					),
					re.sub( ' {2,}', ' ', results['items'][0]['snippet'].encode( 'ascii', 'ignore' ) ),
					'Meer resultaten: http://www.google.nl/search?q={0}'.format( query )
				]
			else:
				return [ "I'm afraid I can't find that." ]
