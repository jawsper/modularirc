from ._module import _module

class quote( _module ):		
	def cmd_quote( self, args, source, target, admin ):
		"""!quote: to get a random quote"""
		return [ self.__random_quote() ]
	
	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( self.get_config( 'quote_file' ) ) as fd:
				return random.choice( fd.readlines() )
		except IOError:
			return 'Error: quote file not found'
		except:
			return 'Error: no quote file defined'
