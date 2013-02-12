#!/usr/bin/env python

from __future__ import print_function

import os, signal, ConfigParser, sys
from MyLovelyIRCBot import MyLovelyIRCBot

#modules
import modules

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
				print( "Error: Erroneous port." )
				sys.exit(1)
		else:
			port = 6667
	
		password = config.get( "main", "password" )
		self.bot = MyLovelyIRCBot( config.get( "main", "channel" ), config.get( "main", "nickname" ), server, port, password )
		self.bot.set_admin( config.get( "main", "admin" ) )
		for module in modules.getmodules():
			self.bot.add_module( modules.getmodule( module )( config.items( module ) ) )
		signal.signal( signal.SIGINT, self.sigint_handler )

	def start( self ):
		print( "Starting botje" )
		self.bot.start()
	def stop( self ):
		print( 'Shutting down botje' )
		self.bot.die()
	def sigint_handler( self, signal, frame ):
		print( 'Ctrl+C pressed, shutting down!' )
		self.stop()
		sys.exit(0)
	
if __name__ == '__main__':
	print( "Welcome to botje" )
	botje = Bot()
	botje.start()
