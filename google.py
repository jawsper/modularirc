# for google_result
import os, httplib, json, pickle, re

class google:
	google_cache_file = os.path.expanduser( '~/.google_cache' )
	google_cache = {}
	api_key = None
	cx = None
	
	def __init__( self, config ):
		for ( k, v ) in config:
			if k == 'api_key':
				self.api_key = v
			elif k == 'cx':
				self.cx = v

		if not os.path.exists( self.google_cache_file ):
			with open( self.google_cache_file, 'w' ) as f:
				pass
		with open( self.google_cache_file, 'rb' ) as f:
			try:
				self.google_cache = pickle.load( f )
			except EOFError:
				pass
				
	def handle_cmd( self, cmd ):
		return self.api_key and self.cx and cmd == 'google'
		
	def handle( self, cmd, args, nick, admin ):
		query = "+".join( args )
	
		if not query in self.google_cache:
			host = "www.googleapis.com"
			path = "{0}?cx={1}&key={2}&q={3}".format( "/customsearch/v1", self.cx, self.api_key, query )
			conn = httplib.HTTPSConnection( host )
			conn.request( "GET", path )
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
				re.sub( r' {2,}', r' ', results['items'][0]['snippet'].encode( 'ascii', 'ignore' ) ),
				'Meer resultaten: http://www.google.nl/?q={0}'.format( query )
			]
		else:
			return [ "I'm afraid I can't find that." ]
