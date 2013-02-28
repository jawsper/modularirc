#!/usr/bin/env python

from __future__ import print_function
import os, sys
from Bot import Bot
	
if __name__ == '__main__':
	print( "Welcome to botje" )
	try:
		pid = os.fork()
		if pid > 0:
			print( 'Forked into PID {0}'.format( pid ) )
			sys.exit(0)
		sys.stdout = open( '/tmp/ircbot.log', 'w' )
	except OSError as error:
		print( 'Unable to fork. Error: {0} ({1})'.format( error.errno, error.strerror ) )
		sys.exit(1)
	botje = Bot()
	botje.start()
