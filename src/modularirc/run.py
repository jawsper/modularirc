import os
import sys
import logging
import select
import time
from imp import reload
from . import Bot

import modularirc

runtime_dir = os.getenv('XDG_RUNTIME_DIR', '/tmp')
pid_file = os.path.join(runtime_dir, 'ircbot.pid')
logging_file = os.path.join(runtime_dir, 'ircbot.log')
logging_level = logging.INFO
logging_format = '[%(asctime)s] %(levelname)s: %(message)s'


def main():
    argv = sys.argv[1:]

    if os.path.exists(pid_file):
        try:
            pid = int(open(pid_file, 'rt').read())
            os.kill(pid, 0)
            print('PID file exists! If the bot is not running, please delete this file before trying to start again!')
            sys.exit(1)
        except ValueError:
            print("Invalid PID file! Assuming it's invalid and deleting it.")
            os.remove(pid_file)
        except ProcessLookupError:
            print("PID in PID file doesn't exist! Deleting PID file and continuing.")
            os.remove(pid_file)
        except:
            print("Can't read PID file!")
            sys.exit(1)
    fork = False
    if len(argv) > 0:
        if argv[0] == '-fork':
            fork = True
    if fork:
        logging.basicConfig(filename=logging_file, level=logging_level, format=logging_format)
    else:
        logging.basicConfig(level=logging_level, format=logging_format)
    logging.info('Welcome to botje')
    if fork:
        try:
            pid = os.fork()
            if pid > 0:
                logging.info('Forked into PID {0}'.format(pid))
                with open(pid_file, 'w') as f:
                    f.write(str(pid))
                print(pid)
                return 0
        except OSError as error:
            logging.error('Unable to fork. Error: {0} ({1})'.format(error.errno, error.strerror))
            return 1
    botje = Bot.Bot()
    while True:
        try:
            logging.info('Starting bot...')
            botje.start()
        except modularirc.BotRestartException:
            continue
        except modularirc.BotReloadException:
            logging.info('Force reloading Bot class')
            botje = None
            reload(Bot)
            botje = Bot.Bot()
            botje.modules.reload_modules()
            continue
        except select.error as e:
            logging.exception('select.error')
            continue
        except (KeyboardInterrupt, modularirc.BotExitException):
            botje.die()
            break
        logging.warning('Botje died, restarting in 5...')
        time.sleep(5)
    logging.info('Exiting bot...')
    if fork:
        os.remove(pid_file)
