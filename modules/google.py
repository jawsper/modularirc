
import os, json, pickle, re
import http.client, urllib.request, urllib.parse, urllib.error
from ._module import _module

class google( _module ):
	"""Bot module to search on google"""
	google_cache_file = os.path.expanduser( '~/.google_cache' )
	
	def __init__( self, mgr ):
		_module.__init__( self, mgr )
		
		self.api_key = self.cx = None
		
		try:
			self.api_key = self.get_config( 'api_key' )
			self.cx = self.get_config( 'cx' )
		except:
			raise Exception

		if not os.path.exists( self.google_cache_file ):
			with open( self.google_cache_file, 'w' ):
				pass
		with open( self.google_cache_file, 'rb' ) as f:
			try:
				self.google_cache = pickle.load( f )
			except EOFError:
				self.google_cache = {}

	def admin_cmd_google_clear_cache( self, args, source, target, admin ):
		"""!google_cache_clear: Clear the google cache"""
		if not admin:
			return
		self.google_cache = {}
	
	def cmd_google( self, args, source, target, admin ):
		"""!google <query>: Search on google"""
		if not self.api_key and self.cx:
			return
			
		query = ' '.join( args )

		if not query in self.google_cache:
			conn = http.client.HTTPSConnection( 'www.googleapis.com' )
			conn.request(
				'GET',
				'/customsearch/v1?' + urllib.parse.urlencode({
					'cx': self.cx,
					'key': self.api_key,
					'q': query
				})
			)
			response = conn.getresponse().read().decode('utf-8')

			self.google_cache[ query ] = json.loads( response )
			with open( self.google_cache_file, 'wb' ) as f:
				pickle.dump( self.google_cache, f )

		results = self.google_cache[ query ]
		if 'items' in results and results['items'] and results['items'][0]:
			snippet = re.sub('[\r\n]', ' ', results['items'][0]['snippet'])
			snippet = snippet.replace('  ', ' ')
			return [
				"{0}: {1}".format(
					results['items'][0]['title'],
					results['items'][0]['link']
				),
				re.sub( ' {2,}', ' ', snippet),
				'Meer resultaten: http://www.google.nl/search?q={0}'.format( '+'.join( args ) )
			]
		else:
			return [ "I'm afraid I can't find that." ]
