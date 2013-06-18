#!/usr/bin/env python3

import os, sys
import Bot
import logging

from imp import reload

pid_file = 'ircbot.pid'
logging_level = logging.DEBUG
logging_format = '[%(asctime)s] %(levelname)s: %(message)s'
	
if __name__ == '__main__':
	if os.path.exists( pid_file ):
		print( 'PID file exists! If the bot is not running, please delete this file before trying to start again!' )
		sys.exit( 1 )
	fork = True
	if len( sys.argv ) > 1:
		if sys.argv[1] == '-nofork':
			fork = False
	if fork:
		logging.basicConfig( filename = 'ircbot.log', level = logging_level, format = logging_format )
	else:
		logging.basicConfig( level = logging_level, format = logging_format )
	logging.info( "Welcome to botje" )
	if fork:
		try:
			pid = os.fork()
			if pid > 0:
				logging.info( 'Forked into PID {0}'.format( pid ) )
				with open( pid_file, 'w' ) as f:
					f.write( pid )
				sys.exit(0)
		except OSError as error:
			logging.error( 'Unable to fork. Error: {0} ({1})'.format( error.errno, error.strerror ) )
			sys.exit(1)
	botje = Bot.Bot()
	while True:
		try:
			botje.start()
		except ( KeyboardInterrupt, Bot.BotExitException ):
			botje.die()
			logging.info( 'Exiting bot...' )
			break
		except Bot.BotReloadException:
			logging.info( 'Force reloading Bot class' )
			botje = None
			reload( Bot )
			botje = Bot.Bot()
			continue
		logging.info( 'Botje died, restarting in 5...' )
		import time
		time.sleep( 5 )
	if fork: os.remove( pid_file )