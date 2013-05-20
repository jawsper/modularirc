from __future__ import print_function
import ConfigParser, sys, os, signal, subprocess
import datetime,time
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_uh, is_channel
import socket
import modules
import sqlite3

from ModuleManager import ModuleManager

class BotReloadException(Exception):
	pass

def print( *args ):
	sys.stdout.write( datetime.datetime.now().strftime( '[%H:%M:%S.%f] ' ) )
	sys.stdout.write( *args )
	sys.stdout.write( '\n' )

class Bot( SingleServerIRCBot ):
	"""The main brain of the IRC bot."""
	def __init__( self ):
		self.last_msg = -1
		self.msg_flood_limit = 0.25
		
		self.admin_channels = []
		self.config = ConfigParser.SafeConfigParser()
		self.__reload_config()
		
		self.db = sqlite3.connect( os.path.join( os.path.dirname( __file__ ), 'ircbot.sqlite3' ) )
		cursor = self.db.cursor()
		try:
			cursor.execute( 'select * from config limit 1' )
		except sqlite3.OperationalError: # table no exist
			cursor.execute( 'create table config ( `group` varchar(100), `key` varchar(100), `value` varchar(100) NULL )' )
		cursor.close()
		self.modules = ModuleManager( self )

		self.channel_ops = {}
		
		s = self.config.get( "main", "server" ).split( ":", 1 )
		server = s[0]
		if len(s) == 2:
			try:
				port = int( s[1] )
			except ValueError:
				print( "Error: Erroneous port." )
				sys.exit(1)
		else:
			port = 6667

		try:
			password = self.config.get( "main", "password" )
		except:
			password = None

		channel = self.config.get( 'main', 'channel' )
		nickname = self.config.get( 'main', 'nickname' )

		if password != None:
			SingleServerIRCBot.__init__( self, [( server, port, password )], nickname, nickname )
		else:
			SingleServerIRCBot.__init__( self, [( server, port )], nickname, nickname )
		
		self.channel = channel
		
		self.load_modules()
		
		signal.signal( signal.SIGINT, self.sigint_handler )
		
	#override
	def start( self ):
		self._connect()
		
		if not self.connection.connected:
			print( 'Failed to connect' )
			return False
		
		self.last_ping = None
		self.ping_timeout = 3 * 60 # 3 minutes
		while self.connection.connected:
			try:
				self.connection.process_data()
			except socket.timeout:
				print( 'Socket timeout' )
				return False
			except BotReloadException as e:
				self.connection.disconnect( "Reloading bot..." )
				raise e
			#except Exception as e:
			#	raise e
			#	print( 'Exception: {0}'.format( e ) )
			
	def __module_handle( self, handler, *args ):
		handler = 'on_' + handler
		for module in self.modules.get_loaded_modules().itervalues():
			if hasattr( module, handler ):
				getattr( module, handler )( *args )
		
	def on_join( self, c, e ):
		self.connection.names( [e.target()] )

	def on_mode( self, c, e ):
		self.connection.names( [e.target()] )

	def on_namreply( self, c, e ):
		chan = e.arguments()[1]
		people = e.arguments()[2].split( ' ' )
		ops = map( lambda p: p[1:], filter( lambda p: p[0] == '@', people ) )
		self.channel_ops[ chan ] = ops
	
	def die( self ):
		self.modules.unload()
		SingleServerIRCBot.die(self)

	def __reload_config( self ):
		self.config.read( os.path.expanduser( "~/.ircbot" ) )
		self.admin = self.config.get( 'main', 'admin' ).split( ';' )
		self.admin_channels = self.config.get( 'main', 'admin_channels' ).split( ';' )

	def load_modules( self, reload = False ):
		"""Find and load all modules.
		Arguments:
		reload: force reload of config and modules
		"""
		if reload:
			self.__reload_config()
		for module_name in self.modules.get_loaded_modules().iterkeys():
			self.modules.disable_module( module_name )
		for module_name in self.modules.get_available_modules():
			self.modules.enable_module( module_name )

	def __add_module( self, module, reload = False ):
		"""Add named module to loaded modules.
		Arguments:
		module: the name of the module
		reload: force reload of the module
		"""
		self.modules.reload_module( module )

	def sigint_handler( self, signal, frame ):
		"""Handle SIGINT to shutdown gracefully with Ctrl+C"""
		print( 'Ctrl+C pressed, shutting down!' )
		self.die()
		sys.exit(0)

	def on_nicknameinuse( self, c, e ):
		"""Gets called if the server complains about the name being in use. Tries to set the nick to nick + '_'"""
		print( "on_nicknameinuse" )
		c.nick( c.get_nickname() + "_" )

	def on_welcome( self, c, e ):
		print( "on_welcome" )
		c.join( self.channel )


#	def on_disconnect( self, c, e ):
#		print( "on_disconnect" )

	def __prevent_flood( self ):
		if self.last_msg > 0:
			if time.time() < self.last_msg + self.msg_flood_limit:
				sleep_time = self.last_msg + self.msg_flood_limit - time.time()
				print( 'Need to sleep for {0}'.format( sleep_time ) )
				time.sleep( sleep_time )
		self.last_msg = time.time()
		
	def notice( self, target, message ):
		self.__prevent_flood()
		self.connection.notice( target, message )
	def privmsg( self, target, message ):
		self.__prevent_flood()
		self.connection.privmsg( target, message )
	def action( self, target, message ):
		self.__prevent_flood()
		self.connection.action( target, message )

	def __process_command( self, c, e ):
		"""Process a message coming from the server."""
		message = e.arguments()[0]
		# commands have to start with !
		if message[0] != '!':
			return
		# strip the ! off, and split the message
		args = message[1:].split()
		# cmd is the first item
		cmd = args.pop(0).strip()
		# test for admin
		admin = nm_to_uh( e.source() ) in self.admin
		if not admin:
			if e.target() in self.admin_channels and e.target() in self.channel_ops and nm_to_n( e.source() ) in self.channel_ops[ e.target() ]:
				admin = True

		# nick is the sender of the message, target is either a channel or the sender.
		source = nm_to_n( e.source() )
		target = e.target()
		if not is_channel( target ):
			target = source

		# see if there is a module that is willing to handle this, and make it so.
		print( '__process_command (src: {0}; tgt: {1}; cmd: {2}; args: {3}; admin: {4})'.format( source, target, cmd, args, admin ) )

		# handle die outside of module (in case module is dead :( )
		if admin:
			if cmd == 'die':
				self.notice( source, 'Goodbye cruel world!' )
				self.die()
				return
			elif cmd == 'restart_class':
				raise BotReloadException
			# config commands
			elif cmd == 'get_config' and len( args ) == 2:
				try:
					value = self.get_config( args[0], args[1] )
					self.notice( source, 'config[{0}][{1}] = {2}'.format( args[0], args[1], value ) )
				except:
					self.notice( source, 'config[{0}][{1}] not set'.format( *args ) )
			elif cmd == 'set_config' and len( args ) == 3:
				try:
					self.set_config( *args )
					self.notice( source, 'Set config setting' )
				except Exception as e:
					self.notice( source, 'Failed setting config setting: {0}'.format( e ) )
			# modules commands
			elif cmd == 'modules':
				self.notice( source, 'Modules: {0}'.format( ', '.join( self.modules.get_modules() ) ) )
			elif cmd == 'available_modules':
				self.notice( source, 'Available modules: ' + ', '.join( self.modules.get_available_modules() ) )
			elif cmd == 'reload_module' and len( args ) > 0:
				for m in args:
					self.notice( source, self.modules.reload_module( m ) )
			elif cmd == 'enable_module' and len( args ) > 0:
				for m in args:
					self.notice( source, self.modules.enable_module( m ) )
			elif cmd == 'disable_module' and len( args ) > 0:
				for m in args:
					self.notice( source, self.modules.disable_module( m ) )
			# other base admin commands
			elif cmd == 'raw':
				self.connection.send_raw( ' '.join( args ) )
				return
			elif cmd == 'admins':
				self.notice( source, 'Current operators:' )
				self.notice( source, ' - global: {0}'.format( ' '.join( self.admin ) ) )
				for chan in [ chan for chan in self.admin_channels if chan in self.channel_ops ]:
#					if not chan in self.channel_ops:
#						continue
					self.notice( source, ' - {0}: {1}'.format( chan, ' '.join( self.channel_ops[ chan ] ) ) )
				return
		
		if cmd == 'help':
			self.notice( target, '!help: this help text' )
		elif admin and cmd == 'admin_help':
			self.notice( source, '!die:                                   kill the bot' )
			self.notice( source, '!raw:                                   send raw irc command' )
			self.notice( source, '!admins:                                see who are admin' )
			self.notice( source, '!restart_class:                         restart the main Bot class' )
			self.notice( source, '!available_modules:                     see modules that are not currently loaded' )
			self.notice( source, '!enable_module <module>[ <module>...]:  enable one or more modules' )
			self.notice( source, '!disable_module <module>[ <module>...]: disable one or more modules' )

		for ( module_name, module ) in self.modules.get_loaded_modules().iteritems():
			try:
				if cmd == 'help' or module.can_handle( cmd, admin ):
					lines = module.handle( cmd, args, source, target, admin )
					if lines:
						for line in lines:
							self.notice( target, line )
			except Exception as e:
				print( "Module '{0}' handle error: {1}".format( module_name, e ) )

	def on_privmsg( self, c, e ):
		#print( "on_privmsg" )
		
		source = nm_to_n( e.source() )
		target = e.target() if is_channel( e.target() ) else source
		message = e.arguments()[0]
		
		self.__module_handle( 'privmsg', source, target, message )
		self.__process_command( c, e )

	def on_pubmsg( self, c, e ):
		#print( "on_pubmsg" )
		self.on_privmsg( c, e )

	def get_config( self, group, key = None ):
		"""gets a config value"""
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
				raise Exception
			return value[0]

	def set_config( self, group, key, value ):
		"""sets a config value"""
		cursor = self.db.cursor()
		data = { 'group': group, 'key': key, 'value': value }
		try:
			self.get_config( group, key )
			cursor.execute( 'update config set `value` = :value where `group` = :group and `key` = :key', data )
		except:
			cursor.execute( 'insert into config ( `group`, `key`, `value` ) values( :group, :key, :value )', data )
		cursor.close()
		self.db.commit()
