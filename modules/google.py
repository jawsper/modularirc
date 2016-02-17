
import os, json, pickle, re
import http.client, urllib.request, urllib.parse, urllib.error
from modules import Module

class google(Module):
	"""Bot module to search on google"""
	google_cache_file = os.path.expanduser( '~/.google_cache' )

	def start(self):
		self.api_key = self.cx = None

		try:
			self.api_key = self.get_config( 'api_key' )
			self.cx = self.get_config( 'cx' )
		except:
			raise Exception

		self.load_cache()

	def load_cache(self):
		if not os.path.exists( self.google_cache_file ):
			with open( self.google_cache_file, 'w' ):
				pass
		with open( self.google_cache_file, 'rb' ) as f:
			try:
				self.google_cache = pickle.load(f)
				if not isinstance(self.google_cache, dict):
					self.google_cache = {}
			except EOFError:
				self.google_cache = {}

	def save_cache(self):
		with open(self.google_cache_file, 'wb') as f:
			pickle.dump(self.google_cache, f)

	def admin_cmd_google_clear_cache(self, admin, **kwargs):
		"""!google_cache_clear: Clear the google cache"""
		if not admin:
			return
		self.google_cache = {}
	
	def cmd_google(self, raw_args, **kwargs):
		"""!google <query>: Search on google"""
		if not self.api_key and self.cx:
			return
			
		query = raw_args

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
			self.save_cache()

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
				'Meer resultaten: http://www.google.nl/search?q={0}'.format(query.replace(' ', '+'))
			]
		else:
			return [ "I'm afraid I can't find that." ]
