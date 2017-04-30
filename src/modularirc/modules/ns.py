import requests
import urllib.parse
import xml.etree.ElementTree as ET
import base64
from datetime import datetime
from dateutil.tz import tzlocal
import dateutil.parser
import logging

from modularirc import BaseModule


class NsApiException(Exception):
    pass

class Module(BaseModule):
    """ns: Bot module to use the NS (Nederlandse Spoorwegen) API"""
    def start(self):
        self.username = self.password = None
        
        try:
            self.username = self.get_config( 'username' )
            self.password = self.get_config( 'password' )
        except:
            return
        
        try:
            self.stations = self.__station_list()
        except Exception as e:
            logging.exception('Loading stations failed')
        
    def cmd_ns(self, arglist, **kwargs):
        """!ns <command>: search train connections (send !ns help for more details)"""
        if len( arglist ) > 0 and arglist[0] != 'help':
            try:
                subcmd = arglist[0]
                args = arglist[1:]
                strarg = ' '.join( args )
                if subcmd == 'plan':
                    return self.__plan_route( args )
                elif subcmd == 'vtijden':
                    if len( strarg ) == 0:
                        strarg = 'enschede'
                    return self.__vertrektijden( strarg )
                elif subcmd == 'storing':
                    return self.__storingen( strarg )
            except:
                logging.exception('Error in NS module.')
                return [ 'Bot error\'d :(' ]
        return [
            'Usage: !ns <command> <arguments>',
            'Commands:',
            'help (no arguments): this help text',
            'plan (<fromStation> [<viaStation>] <toStation>): plan route from a to b (optionally via c)',
            'vtijden [<station>]: departure times (default Enschede)',
            'storing [<station>]: storingen (station optioneel)'
        ]

    def __apiquery( self, api_method, args = None ):
        try:
            url = urllib.parse.urlunsplit(('http', 'webservices.ns.nl', api_method, urllib.parse.urlencode(args) if args and len(args) > 0 else '', ''))
            response = requests.get(url, headers={
                'Authorization': 'Basic ' + base64.b64encode('{0}:{1}'.format(self.username, self.password).encode('utf-8')).decode('utf-8')
                })
            root = ET.fromstring(response.text)
            if root.tag == 'error':
                raise NsApiException('API error: {0}'.format(root[0].text))
            return root
        except:
            raise NsApiException('Unable to connect to API.')
    
    def __station_list( self ):
        try:
            root = self.__apiquery( 'ns-api-stations-v2' )
        except NsApiException as e:
            return [ str( e ) ]
        if root.tag == 'Stations':
            list = {}
            for station in root:
                namen = []
                code = station.find( 'Code' ).text
                land = station.find( 'Land' ).text
                for naam in station.find( 'Namen' ):
                    if not naam.text in namen:
                        namen.append( naam.text )
                for naam in station.find( 'Synoniemen' ):
                    if not naam.text in namen:
                        namen.append( naam.text )
                list[ code ] = {
                    'land': land,
                    'namen': namen
                }
            return list
        raise Exception
    
    def __get_station_code( self, arg ):
        for code in self.stations:
            for name in self.stations[ code ]['namen']:
                if name.lower() in arg:
                    return ( code, name.lower() )
        return ( False, False )
    
    def __make_station_search_args( self, args ):
        list = []
        for i in range( 0, len( args ) + 1 ):
            list.append( ' '.join( args[ :i ] ) )
        return list
    
    def __plan_route( self, args ):
        fromStation = toStation = viaStation = None
        
        args = [x.lower() for x in args]
        
        codes = []
        
        while len( args ) > 0:
            search = self.__make_station_search_args( args )
            ( code, match ) = self.__get_station_code( search )
            if code:
                codes.append( code )
                args = args[ len( match.split( ' ' ) ) : ]
            else:
                args = args[ 1 : ]
        
        if len( codes ) < 2:
            return [ 'Error: niet genoeg stations opgegeven' ]
        
        fromStation = codes[0]
        toStation = codes[1]
        if len( codes ) > 2:
            viaStation = codes[1]
            toStation = codes[2]
        
        if not ( fromStation and toStation ):
            return [ 'Error: geen geldige stations opgegeven.' ]
        if fromStation == toStation and not viaStation:
            return [ 'Error: fromStation en toStation zijn gelijk en er is geen viaStation' ]
        try:
            args = {
                'previousAdvices': 0,
                'nextAdvices': 2,
                'fromStation': fromStation,
                'toStation': toStation
            }
            if viaStation:
                args['viaStation'] = viaStation
            
            root = self.__apiquery( 'ns-api-treinplanner', args )
        except NsApiException as e:
            return [ str( e ) ]
        
        if root.tag == 'ReisMogelijkheden':
            now = datetime.now(tzlocal())
            response = []
            i = 0
            max_results = 3
            for rm in root:
                ( vertrektijd, vertrektijd_delta ) = self.__parse_tijd( rm.find( 'ActueleVertrekTijd' ).text, now )
                reistijd = rm.find( 'ActueleReisTijd' ).text
                overstappen = rm.find( 'AantalOverstappen' ).text
                response.append(
                    '#{0}: Reistijd {1}; {2} overstappen; vertrekt om {3} (over {4})'.format( 
                        i, reistijd, overstappen, vertrektijd, vertrektijd_delta
                    )
                )
                reisdelen = []
                curr = None
                max_part_len = ( [ 0, 0, 0 ], [ 0, 0, 0 ] )
                for reisdeel in rm.findall( 'ReisDeel' ):
                    stops = [[
                            self.__parse_tijd( x.find( 'Tijd' ).text ),
                            x.find( 'Naam' ).text,
                            'sp ' + x.find( 'Spoor' ).text if x.find( 'Spoor' ) is not None else None
                        ] if x is not None else None for x in reisdeel.findall( 'ReisStop' )]
                    a = stops[0]
                    b = stops[-1]
                    
                    for j in range( 0, 3 ):
                        if len( a[j] ) > max_part_len[0][j]:
                            max_part_len[0][j] = len( a[j] )
                        if len( b[j] ) > max_part_len[1][j]:
                            max_part_len[1][j] = len( b[j] )
                    
                    reisdelen.append( ( a, b ) )
                
                for ( a, b ) in reisdelen:
                    for j in range( 0, 3 ):
                        a[j] = a[j].ljust( max_part_len[0][j] )
                        b[j] = b[j].ljust( max_part_len[1][j] )
                    fmt = '{0}  {1}  {2}'
                    a = fmt.format( *a )
                    b = fmt.format( *b )
                    response.append(
                        '    | In: {0} | Uit: {1} |'.format( a, b )
                    )
                i += 1
                if i >= max_results:
                    break
            if len( response ) == 0:
                return [ 'Geen resultaten...' ]
            return response
        raise Exception()
    
    def __vertrektijden( self, station ):
        try:
            root = self.__apiquery( 'ns-api-avt', { 'station': station } )
        except NsApiException as e:
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
            root = self.__apiquery( 'ns-api-storingen', { 'station': station } )
        except NsApiException as e:
            return [ str(e) ]
        
        if root.tag == 'Storingen':
            response = []
            #for storing in root.find( 'Ongepland' ):
            #   pass
            for storing_type in root:
                response.append( '{0}:'.format( storing_type.tag ) )
                for storing in storing_type:
                    traject = storing.find( 'Traject' ).text
                    response.append( '\t* {0}'.format(
                        traject
                    ) )
                else:
                    response.append( '\t* Geen' )
            return response
        raise Exception()
    
    def __parse_tijd( self, time_str, now = None ):
        tijd_datetime = dateutil.parser.parse( time_str )
        if not now:
            return tijd_datetime.strftime( '%H:%M' )
        tijd_delta = tijd_datetime - now
        minuten = tijd_delta.seconds // 60
        uren = minuten // 60
        minuten %= 60
        if uren > 0:
            tijd_delta = '{0} uur, {1} minuten'.format( uren, minuten )
        else:
            tijd_delta = '{0} minuten'.format( minuten )
        return ( tijd_datetime.strftime( '%H:%M' ), tijd_delta )
        
