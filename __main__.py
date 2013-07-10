#!/usr/bin/env python3

import os, sys
import Bot
import logging
import select

from imp import reload

pid_file = os.path.join( os.path.dirname( __file__ ), 'ircbot.pid' )
logging_file = os.path.join( os.path.dirname( __file__ ), 'ircbot.log' )
logging_level = logging.DEBUG
logging_format = '[%(asctime)s] %(levelname)s: %(message)s'

if __name__ == '__main__':
	if os.path.exists( pid_file ):
		print( 'PID file exists! If the bot is not running, please delete this file before trying to start again!' )
		sys.exit( 1 )
	fork = False
	if len( sys.argv ) > 1:
		if sys.argv[1] == '-fork':
			fork = True
	if fork:
		logging.basicConfig( filename = logging_file, level = logging_level, format = logging_format )
	else:
		logging.basicConfig( level = logging_level, format = logging_format )
	logging.info( "Welcome to botje" )
	if fork:
		try:
			pid = os.fork()
			if pid > 0:
				logging.info( 'Forked into PID {0}'.format( pid ) )
				with open( pid_file, 'w' ) as f:
					f.write( str( pid ) )
				print( pid )
				sys.exit(0)
		except OSError as error:
			logging.error( 'Unable to fork. Error: {0} ({1})'.format( error.errno, error.strerror ) )
			sys.exit(1)
	botje = Bot.Bot()
	while True:
		try:
			logging.info( 'Starting bot...' )
			botje.start()
		except Bot.BotReloadException:
			logging.info( 'Force reloading Bot class' )
			botje = None
			reload( Bot )
			botje = Bot.Bot()
			continue
		except select.error:
			continue
		except ( KeyboardInterrupt, Bot.BotExitException ):
			botje.die()
			break
		logging.info( 'Botje died, restarting in 5...' )
		import time
		time.sleep( 5 )
	logging.info( 'Exiting bot...' )
	if fork: os.remove( pid_file )
