from __future__ import print_function
import httplib, urllib
import xml.etree.ElementTree as ET
import traceback
import base64
from datetime import datetime
from dateutil.tz import tzlocal
import dateutil.parser
from _module import _module

class NsApiException(Exception):
	pass

class ns( _module ):
	"""Bot module to use the NS (Nederlandse Spoorwegen) API"""
	def can_handle( self, cmd, admin ):
		return self.username and self.password and cmd == 'ns'
	
	def handle( self, bot, cmd, args, source, target, admin ):
		if cmd == 'help':
			self.bot.privmsg( target, '!ns <command>: search train connections (send !ns help for more details)' )
			return
		if len( args ) > 0 and args[0] != 'help':
			try:
				subcmd = args[0]
				args = args[1:]
				strarg = ' '.join( args )
				if subcmd == 'plan':
					if len( args ) == 0 or ',' not in args[0]:
						return [ 'Usage: !ns plan <fromStation>,<toStation>' ]
					return self.__plan_route( *args[0].split(',') )
				elif subcmd == 'vtijden':
					if len( strarg ) == 0:
						strarg = 'enschede'
					return self.__vertrektijden( strarg )
				elif subcmd == 'storing':
					return self.__storingen( strarg )
			except:
				traceback.print_exc()
				return [ 'Bot error\'d :(' ]
		return [
			'Usage: !ns <command> <arguments>',
			'Commands:',
			'help (no arguments): this help text',
			'plan (<fromStation>,<toStation>): plan route from a to b',
			'vtijden [<station>]: departure times (default Enschede)',
			'storing [<station>]: storingen (station optioneel)'
		]

	def __apiquery( self, api_method, args ):
		conn = httplib.HTTPConnection( 'webservices.ns.nl' )
		conn.request(
			'GET',
			'/{0}{1}'.format( api_method, '?' + urllib.urlencode( args ) if len( args ) > 0 else '' ),
			headers = { 'Authorization': 'Basic ' + base64.b64encode( '{0}:{1}'.format( self.username, self.password ) ) }
		)
		response = conn.getresponse()
		data = response.read()
		conn.close()
		root = ET.fromstring( data )
		if root.tag == 'error':
			raise NsApiException( 'API error: {0}'.format( root[0].text ) )
		return root
			
	def __plan_route( self, fromStation, toStation ):
		try:
			root = self.__apiquery( 'ns-api-treinplanner', {
				'previousAdvices': 0,
				'fromStation': fromStation,
				'toStation': toStation
			})
		except NsApiException, e:
			return [ str( e ) ]
		
		#print( '_search( "{0}", "{1}" )'.format( fromStation, toStation ) )
		if root.tag == 'ReisMogelijkheden':
			now = datetime.now(tzlocal())
			response = []
			i = 0
			for rm in root:
				( vertrektijd, vertrektijd_delta ) = self.__parse_tijd( rm.find( 'ActueleVertrekTijd' ).text, now )
				reistijd = rm.find( 'ActueleReisTijd' ).text
				overstappen = rm.find( 'AantalOverstappen' ).text
				response.append( 
					'#{0}: Reistijd {1}; {2} overstappen; vertrekt om {3} (over {4})'.format( 
						i, reistijd, overstappen, vertrektijd, vertrektijd_delta
					)
				)
				i += 1
			if len( response ) == 0:
				return [ 'Geen resultaten...' ]
			return response
		raise Exception()
	
	def __vertrektijden( self, station ):
		try:
			root = self.__apiquery( 'ns-api-avt', { 'station': station } )
		except NsApiException, e:
			return [ str(e) ]
		if root.tag == 'ActueleVertrekTijden':
			now = datetime.now(tzlocal())
			response = []
			i = 0
			for vt in root:
				if i > 5:
					break
				( vertrektijd, vertrektijd_delta ) = self.__parse_tijd( vt.find( 'VertrekTijd' ).text, now )
				treinsoort = vt.find( 'TreinSoort' ).text
				eindbestemming = vt.find( 'EindBestemming' ).text
				spoor = vt.find( 'VertrekSpoor' )
				spoor_str = spoor.text
				if spoor.attrib['wijziging'] == 'true':
					spoor_str += ' [!]'
				response.append( '#{0} {1} naar {2} op spoor {5}; vertrekt om {3} (over {4})'.format( 
					i, treinsoort, eindbestemming, vertrektijd, vertrektijd_delta, spoor_str 
				) )
				i += 1
			if len( response ) == 0:
				return [ 'Geen resultaten...' ]
			return response
		raise Exception()
	
	def __storingen( self, station ):
		try:
			root = self.__apiquery( 'ns-api-storingen', station )
		except NsApiException, e:
			return [ str(e) ]
		
		if root.tag == 'Storingen':
			response = []
			#for storing in root.find( 'Ongepland' ):
			#	pass
			for storing_type in root:
				response.append( '{0}:'.format( storing_type.tag ) )
				for storing in storing_type:
					traject = storing.find( 'Traject' ).text
					response.append( '\t{0}'.format(
						traject
					) )
			return response
		raise Exception()
	
	def __parse_tijd( self, time_str, now = None ):
		tijd_datetime = dateutil.parser.parse( time_str )
		if not now:
			return tijd_datetime.strftime( '%H:%M' )
		tijd_delta = tijd_datetime - now
		minuten = tijd_delta.seconds / 60
		uren = minuten / 60
		minuten %= 60
		if uren > 0:
			tijd_delta = '{0} uur, {1} minuten'.format( uren, minuten )
		else:
			tijd_delta = '{0} minuten'.format( minuten )
		return ( tijd_datetime.strftime( '%H:%M' ), tijd_delta )
		
