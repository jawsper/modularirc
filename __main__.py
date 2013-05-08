#!/usr/bin/env python

from __future__ import print_function
import os, sys
import Bot
	
if __name__ == '__main__':
	print( "Welcome to botje" )
	fork = True
	if len( sys.argv ) > 1:
		if sys.argv[1] == '-nofork':
			fork = False
	if fork:
		try:
			pid = os.fork()
			if pid > 0:
				print( 'Forked into PID {0}'.format( pid ) )
				sys.exit(0)
			sys.stdout = open( '/tmp/ircbot.log', 'w' )
		except OSError as error:
			print( 'Unable to fork. Error: {0} ({1})'.format( error.errno, error.strerror ) )
			sys.exit(1)
	botje = Bot.Bot()
	while True:
		try:
			botje.start()
		except Bot.BotReloadException:
			print( 'Force reloading Bot class' )
			botje = None
			reload(Bot)
			botje = Bot.Bot()
		print( 'Botje died, restarting in 5...' )
		import time
		time.sleep( 5 )
