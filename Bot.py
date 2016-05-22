import os
import time

import irc.bot
import irc.connection
from irc.client import is_channel
import irc.client
import irc.buffer
irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer

import ssl

import sqlite3
import logging
import json

from modules import ModuleManager

class BotRestartException(Exception):
    pass
class BotReloadException(Exception):
    pass
class BotExitException(Exception):
    pass

class Bot(irc.bot.SingleServerIRCBot):
    """The main brain of the IRC bot."""

    BOT_CFG_KEY = '_Bot'

    def __init__( self ):
        logging.info('Bot __init__')
        self.last_msg = -1
        self.msg_flood_limit = 0.25

        with open(os.path.join(os.path.dirname(__file__), 'ircbot.conf')) as f:
            data = json.load(f)
            self.servers = data['servers']

        self.select_server(0)

        self.db = sqlite3.connect( os.path.join( os.path.dirname( __file__ ), 'ircbot.sqlite3' ), check_same_thread = False )
        cursor = self.db.cursor()
        try:
            cursor.execute( 'select * from config limit 1' )
        except sqlite3.OperationalError: # table no exist
            cursor.execute( 'create table config ( `group` varchar(100), `key` varchar(100), `value` varchar(100) NULL )' )
        cursor.close()
        modules_blacklist = data.get('blacklist', None)
        self.modules = ModuleManager(self, modules_blacklist)

        self.channel_ops = {}

        server = self.current_server['host']
        port = self.current_server['port'] if 'port' in self.current_server else 6667
        ssl_enabled = self.current_server['ssl'] if 'ssl' in self.current_server else False
        ipv6_enabled = self.current_server['ipv6'] if 'ipv6' in self.current_server else False
        password = self.current_server['password'] if 'password' in self.current_server else ''
        nickname = self.current_server['nickname']

        factory = irc.connection.Factory(wrapper=ssl.wrap_socket if ssl_enabled else lambda x: x, ipv6=ipv6_enabled)

        super(Bot, self).__init__([irc.bot.ServerSpec(server, port, password)], nickname, nickname, connect_factory=factory)
        
        self.connection.set_rate_limit(30)

        for module_name in self.modules.get_available_modules():
            self.modules.enable_module( module_name )

    def select_server(self, index):
        self.current_server = self.servers[index]

        self.admin = self.current_server['global_admins']
        self.admin_channels = self.current_server['admin_channels']

    def start( self ):
        logging.debug( 'start()' )
        super(Bot, self).start()

    def die( self ):
        logging.debug( 'die()' )
        self.modules.unload()
        self.connection.disconnect( 'Bye, cruel world!' )
        #super(Bot, self).die()

    def __process_message(self, message):
        for char in '\r\n': message = message.replace(char, '')
        MAX_MESSAGE_COUNT = 5
        MAX_LINE_LEN = 256
        m = []
        for i in range(0, len(message), MAX_LINE_LEN):
            if len(m) >= MAX_MESSAGE_COUNT:
                m.append('(message truncated) ...')
                break
            m.append(message[i:i + MAX_LINE_LEN])
        return m
    def notice( self, target, message ):
        for m in self.__process_message(message):
            self.connection.notice(target, m)
    def privmsg( self, target, message ):
        for m in self.__process_message(message):
            self.connection.privmsg(target, m)
    def action( self, target, message ):
        for m in self.__process_message(message):
            self.connection.action(target, m)

    def __module_handle(self, handler, **kwargs):
        """Passed the "on_*" handlers through to the modules that support them"""
        handler = 'on_' + handler
        for (_ , module) in self.modules.get_loaded_modules():
            if hasattr(module, handler):
                try:
                    getattr(module, handler)(**kwargs)
                except Exception as e:
                    logging.debug('Module handler %s.%s failed: %s', _, handler, e)

    def __process_command( self, c, e ):
        """Process a message coming from the server."""
        message = e.arguments[0]
        # commands have to start with !
        if message[0] != '!':
            return
        # strip the ! off, and split the message into command and arguments
        split_message = message[1:].split(None, 1)
        cmd = split_message.pop(0).strip()
        raw_args = split_message[0] if len(split_message) else ''
        arglist = raw_args.split()

        # test for admin
        admin = e.source.userhost in self.admin
        if not admin:
            if e.target in self.admin_channels and e.target in self.channel_ops and e.source.nick in self.channel_ops[ e.target ]:
                admin = True

        # nick is the sender of the message, target is either a channel or the sender.
        source = e.source.nick
        target = e.target if is_channel(e.target) else source

        # see if there is a module that is willing to handle this, and make it so.
        logging.debug( '__process_command (src: %s; tgt: %s; cmd: %s; args: %s; admin: %s)', source, target, cmd, raw_args, admin )

        # handle die outside of module (in case module is dead :( )
        if admin:
            if cmd == 'die':
                self.notice( source, 'Goodbye cruel world!' )
                raise BotExitException
            elif cmd == 'jump':
                self.jump_server()
            elif cmd == 'restart_class':
                self.notice(source, 'Restarting...')
                raise BotReloadException
            # config commands
            elif cmd == 'get_config' and len( arglist ) <= 2:
                if len( arglist ) == 2:
                    try:
                        value = self.get_config( arglist[0], arglist[1] )
                        self.notice( source, 'config[{0}][{1}] = {2}'.format( arglist[0], arglist[1], value ) )
                    except:
                        self.notice( source, 'config[{0}][{1}] not set'.format( *arglist ) )
                elif len( arglist ) == 1:
                    try:
                        values = self.get_config( arglist[0] )
                        if len( values ) > 0:
                            self.notice( source, 'config[{}]: '.format( arglist[0] ) + ', '.join( [ '{}: "{}"'.format( k,v ) for ( k, v ) in values.items() ] ) )
                        else:
                            self.notice( source, 'config[{}] is empty'.format( arglist[0] ) )
                    except:
                        self.notice( source, 'config[{}] not set'.format( arglist[0] ) )
                else:
                    try:
                        self.notice( source, 'config groups: ' + ', '.join( self.get_config_groups() ) )
                    except Exception as e:
                        self.notice( source, 'No config groups: {}'.format( e ) )
            elif cmd == 'set_config' and len( arglist ) >= 2:
                if len( arglist ) >= 3:
                    config_val = ' '.join( arglist[2:] )
                else:
                    config_val = None
                try:
                    self.set_config( arglist[0], arglist[1], config_val )
                    self.notice( source, 'Set config setting' if config_val else 'Cleared config setting' )
                except Exception as e:
                    self.notice( source, 'Failed setting/clearing config setting: {0}'.format( e ) )
            # other base admin commands
            elif cmd == 'raw':
                self.connection.send_raw(raw_args)
                return
            elif cmd == 'admins':
                self.notice( source, 'Current operators:' )
                self.notice( source, ' - global: {0}'.format( ' '.join( self.admin ) ) )
                for chan in [ chan for chan in self.admin_channels if chan in self.channel_ops ]:
                    self.notice( source, ' - {0}: {1}'.format( chan, ' '.join( self.channel_ops[ chan ] ) ) )
                return

        if False and cmd == 'help':
            if len( arglist ) > 0:
                if arglist[0] == 'module':
                    if len( arglist ) < 2:
                        pass
                    elif self.modules.module_is_loaded( arglist[1] ):
                        module = self.modules.get_module( arglist[1] )
                        self.notice( target, module.__doc__ )
                else:
                    for ( module_name, module ) in self.modules.get_loaded_modules():
                        if module.has_cmd( arglist[0] ):
                            self.notice( target, module.get_cmd( arglist[0] ).__doc__ )
            else:
                self.notice( target, '!help: this help text (send !help <command> for command help, send !help module <module> for module help)' )
                for ( module_name, module ) in [ lst for lst in self.modules.get_loaded_modules() if lst[1].has_commands and not lst[1].admin_only ]:
                    cmds = module.get_cmd_list()
                    self.notice( target, ' * {0}: {1}'.format( module_name, ', '.join( cmds ) if len( cmds ) > 0 else 'No commands' ) )

        elif False and admin and cmd == 'admin_help':
            if len( arglist ) > 0:
                for ( module_name, module ) in self.modules.get_loaded_modules():
                    if module.has_admin_cmd( arglist[0] ):
                        self.notice( source, module.get_admin_cmd( arglist[0] ).__doc__ )
            else:
                self.notice( source, '!admin_help: this help text (send !admin_help <command> for command help' )
                self.notice( source, '!die:                                   kill the bot' )
                self.notice( source, '!raw:                                   send raw irc command' )
                self.notice( source, '!admins:                                see who are admin' )
                self.notice( source, '!restart_class:                         restart the main Bot class' )
                for ( module_name, module ) in self.modules.get_loaded_modules():
                    cmds = module.get_admin_cmd_list()
                    if len( cmds ) > 0:
                        self.notice( source, ' * {0}: {1}'.format( module_name, ', '.join( cmds ) ) )
        else:
            for ( module_name, module ) in self.modules.get_loaded_modules():
                try:
                    if module.has_cmd( cmd ):
                        lines = module.get_cmd( cmd )(args=arglist, arglist=arglist, raw_args=raw_args, source=source, target=target, admin=admin)
                        if lines:
                            for line in lines:
                                self.notice( target, line )
                    elif admin and module.has_admin_cmd( cmd ):
                        lines = module.get_admin_cmd(cmd)(args=arglist, arglist=arglist, raw_args=raw_args, source=source, target=target, admin=admin)
                        if lines:
                            for line in lines:
                                self.notice( source, line )
                except Exception as e:
                    logging.exception( "Module '{0}' handle error: {1}".format( module_name, e ) )

    def on_privmsg(self, c, e):
        logging.debug("on_privmsg")

        source = e.source.nick
        target = e.target if is_channel( e.target ) else source
        message = e.arguments[0]

        self.__module_handle('privmsg', source=source, target=target, message=message)
        try:
            self.__process_command( c, e )
        except BotExitException as e:
            raise e
        except BotReloadException as e:
            self.connection.disconnect( "Reloading bot..." )
            self.modules.unload()
            raise e
        except Exception as e:
            logging.exception( 'Error in __process_command: %s', e )

    def on_pubmsg(self, c, e):
        logging.debug("on_pubmsg")
        self.on_privmsg(c, e)

    def on_pubnotice(self, c, e):
        self.on_notice( c, e )
    def on_privnotice(self, c, e):
        self.on_notice(c, e)

    def on_notice(self, c, e):
        source = e.source
        target = e.target
        message = e.arguments[0]
        logging.debug('notice! source: {}, target: {}, message: {}'.format(source, target, message))
        self.__module_handle('notice', source=source, target=target, message=message)

    def on_join(self, connection, event):
        self.connection.names([event.target])
        self.__module_handle('join', connection=connection, event=event)

    def on_part(self, c, e):
        self.connection.names([e.target])

    def on_kick(self, c, e):
        self.connection.names([e.target])

    def on_mode( self, c, e ):
        self.connection.names( [e.target] )

    def on_endofnames(self, c, e):
        channel, text = e.arguments
        if not channel in self.channels:
            return
        self.channel_ops[channel] = list(self.channels[channel].opers())

    # def on_nick(self, c, e):
    #     self.connection.names(self.channels.keys())

    def on_nicknameinuse( self, c, e ):
        """Gets called if the server complains about the name being in use. Tries to set the nick to nick + '_'"""
        logging.debug( "on_nicknameinuse" )
        c.nick( c.get_nickname() + "_" )

    def on_welcome(self, connection, event):
        for chan in self.current_server['channels']:
            connection.join( chan )
        self.__module_handle('welcome', connection=connection, event=event)

    def get_config_groups( self ):
        resultset = self.db.execute( 'select distinct `group` from config' )
        return [ g for ( g, ) in resultset.fetchall() ]

    def get_config( self, group, key = None, default = None ):
        """gets a config value"""
        logging.info( 'get config %s.%s', group, key )
        if key == None:
            resultset = self.db.execute( 'select `key`, `value` from config where `group` = :group', { 'group': group } )
            values = {}
            for ( key, value ) in resultset.fetchall():
                values[ key ] = value
            return values
        else:
            resultset = self.db.execute( 'select `value` from config where `group` = :group and `key` = :key', { 'group': group, 'key': key } )
            value = resultset.fetchone()
            if value == None:
                if default != None:
                    return default
                raise Exception('Value not found')
            return value[0]

    def set_config( self, group, key, value ):
        """sets a config value"""
        logging.info( 'set config %s.%s to "%s"', group, key, value )
        cursor = self.db.cursor()
        data = { 'group': group, 'key': key, 'value': value }
        if value == None:
            cursor.execute( 'delete from config where `group` = :group and `key` = :key', data )
        else:
            try:
                self.get_config( group, key )
                cursor.execute( 'update config set `value` = :value where `group` = :group and `key` = :key', data )
            except:
                cursor.execute( 'insert into config ( `group`, `key`, `value` ) values( :group, :key, :value )', data )
        cursor.close()
        self.db.commit()
