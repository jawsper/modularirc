from ._module import _module
import logging
import random

class quote( _module ):
	def cmd_quote( self, args, source, target, admin ):
		"""!quote: to get a random quote"""
		return [ self.__random_quote() ]

	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( self.get_config( 'quote_file' ), 'rt', encoding = 'utf-8' ) as fd:
				return random.choice( fd.readlines() )
		except IOError as e:
			logging.exception( 'Quote IOError' )
			return 'Error: quote file not found: {}'.format( e )
		except:
			logging.exception( 'Quote Exception' )
			return 'Error: no quote file defined'
