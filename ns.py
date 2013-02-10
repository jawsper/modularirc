import httplib
import xml.etree.ElementTree as ET
import traceback
import base64
from datetime import datetime
from dateutil.tz import tzlocal
import dateutil.parser

class ns:
	username = None
	password = None
	def __init__( self, config ):
		for ( k, v ) in config:
			if k == 'username':
				self.username = v
			elif k == 'password':
				self.password = v
	
	def handle_cmd( self, cmd ):
		return self.username and self.password and cmd == 'ns'
	
	def handle( self, cmd, args, nick, admin ):
		if len( args ) != 2:
			return [ "Usage: !ns <fromStation> <toStation>" ]
		else:
			try:
				return self._search( args[0], args[1] )
			except:
				return [ "Errorrrrr. Plz to tell jawsper I failed serving you my liege." ]
	
	def _search( self, fromStation, toStation ):
		conn = httplib.HTTPConnection( 'webservices.ns.nl' )
		conn.request( 
			'GET', 
			'/ns-api-treinplanner?fromStation={0}&toStation={1}&previousAdvices=0'.format( fromStation, toStation )
			, headers = { 'Authorization': 'Basic ' + base64.b64encode( '{0}:{1}'.format( self.username, self.password ) ) }
		)
		response = conn.getresponse()
		data = response.read()
		#print data
		root = ET.fromstring( data )
		if root.tag == 'error':
			return [ 'Fout: {0}'.format( root[0].text ) ]
		elif root.tag == 'ReisMogelijkheden':
			now = datetime.now(tzlocal())
			response = []
			i = 0
			for rm in root:
				vtijd = dateutil.parser.parse( rm.find( 'ActueleVertrekTijd' ).text )
				vertrektijd = vtijd - now
				minuten = vertrektijd.seconds / 60
				vertrektijd = '{0} uur, {1} minuten'.format( minuten / 60, minuten % 60 )
				reistijd = rm.find( 'ActueleReisTijd' ).text
				overstappen = rm.find( 'AantalOverstappen' ).text
				response.append( '#{0}: Reistijd {2}; {3} overstappen; vertrekt over {1}'.format( i, vertrektijd, reistijd, overstappen ) )
				i += 1
			return response
		raise Exception()
