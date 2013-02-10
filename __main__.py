#!/usr/bin/env python

import os, signal, ConfigParser
from MyLovelyIRCBot import MyLovelyIRCBot

#modules
import ns, google

#import irclib
#irclib.DEBUG = 1

class Bot:
	def __init__( self ):
		config = ConfigParser.SafeConfigParser()
		config.read( os.path.expanduser( "~/.ircbot" ) )

		s = config.get( "main", "server" ).split( ":", 1 )
		server = s[0]
		if len(s) == 2:
			try:
				port = int( s[1] )
			except ValueError:
				print "Error: Erroneous port."
				sys.exit(1)
		else:
			port = 6667
	
		password = config.get( "main", "password" )
		self.bot = MyLovelyIRCBot( config.get( "main", "channel" ), config.get( "main", "nickname" ), server, port, password )
		self.bot.set_admin( config.get( "main", "admin" ) )
		self.bot.add_module( ns.ns( config.items( 'ns' ) ) )
		self.bot.add_module( google.google( config.items( 'google' ) ) )

	def start( self ):
		print( "Starting botje" )
		self.bot.start()

botje = None

def signal_handler( signal, frame ):
	global botje
	print 'Ctrl+C pressed, shutting down!'
	botje.bot.die()
	sys.exit(0)
	
if __name__ == '__main__':
	print( "Welcome to botje" )
	signal.signal( signal.SIGINT, signal_handler )
	botje = Bot()
	botje.start()
