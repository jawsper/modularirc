from __future__ import print_function
import ConfigParser, sys, os, signal, subprocess
import datetime,time
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_uh, is_channel
import socket
import modules

class BotReloadException(Exception):
	pass

def print( *args ):
	sys.stdout.write( datetime.datetime.now().strftime( '[%H:%M:%S.%f] ' ) )
	sys.stdout.write( *args )
	sys.stdout.write( '\n' )

class Bot( SingleServerIRCBot ):
	"""The main brain of the IRC bot."""
	def __init__( self ):
		self.modules = {}
		self.admin_channels = []
		self.config = ConfigParser.SafeConfigParser()
		self.__reload_config()

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
			except Exception as e:
				print( 'Exception: {0}'.format( e ) )
			
	def __module_handle( self, handler, e ):
		for mod in self.modules:
			if hasattr( self.modules[ mod ], handler ):
				getattr( self.modules[ mod ], handler )( self, e )
		
	def on_join( self, c, e ):
#		print( "on_join: (t: {0}, s: {1})".format( e.target(), e.source() ) )
		self.connection.names( [e.target()] )

	def on_mode( self, c, e ):
#		print( 'on_mode: {0}, {1}: {2}'.format( e.target(), e.source(), e.arguments() ) )
		self.connection.names( [e.target()] )

	def on_namreply( self, c, e ):
#		print( 'on_namreply: {0}'.format( e.arguments() ) )
		chan = e.arguments()[1]
		people = e.arguments()[2].split( ' ' )
		ops = map( lambda p: p[1:], filter( lambda p: p[0] == '@', people ) )
		self.channel_ops[ chan ] = ops
	
	def die( self ):
		if self.modules:
			for module in self.modules:
				try:
					self.modules[module].stop()
				except Exception as e:
					print( 'Failed to stop module {0}: {1}'.format( module, e ) )
			del self.modules
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
		if self.modules:
			for module in self.modules:
				try:
					self.modules[module].stop()
				except Exception as e:
					print( 'Failed to stop module {0}: {1}'.format( module, e ) )
		self.modules = {}
		for module in modules.getmodules():
			try:
				self.__add_module( module, reload )
			except Exception, e:
				print( "Failed loading module '{0}': {1}".format( module, e ) )

	def __add_module( self, module, reload = False ):
		"""Add named module to loaded modules.
		Arguments:
		module: the name of the module
		reload: force reload of the module
		"""
		if reload:
			modules.reload_module( module )
		try:
			cfg = self.config.items( module )
		except ConfigParser.NoSectionError:
			cfg = {}
		self.modules[ module ] = modules.getmodule( module )( cfg, self )

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

	def notice( self, target, message ):
		self.connection.notice( target, message )
	def privmsg( self, target, message ):
		self.connection.privmsg( target, message )
	def action( self, target, message ):
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
			elif cmd == 'reload_module' and len( args ) > 0:
				for m in args:
					if m in self.modules:
						try:
							self.__add_module( m, True )
						except Exception as e:
							self.notice( source, "Failed loading module '{0}': {1}".format( m, e ) )
			elif cmd == 'available_modules':
				a_m = []
				for module in modules.getmodules():
					if not module in self.modules:
						a_m.append( module )
				self.notice( source, 'Available modules: ' + ', '.join( a_m ) )
			elif cmd == 'enable_module' and len( args ) > 0:
				for m in args:
					if not m in self.modules:
						try:
							self.__add_module( m, True )
						except Exception as e:
							self.notice( source, "Failed loading module '{0}': {1}".format( m, e ) )
			elif cmd == 'disable_module' and len( args ) > 0:
				for m in args:
					if m in self.modules:
						try:
							self.modules[ m ].stop()
						except:
							pass
						del self.modules[ m ]
			elif cmd == 'raw':
				self.connection.send_raw( ' '.join( args ) )
				return
			elif cmd == 'admins':
				self.notice( source, 'Current operators:' )
				self.notice( source, ' - global: {0}'.format( ' '.join( self.admin ) ) )
				for chan in self.admin_channels:
					if not chan in self.channel_ops:
						continue
					self.notice( source, ' - {0}: {1}'.format( chan, ' '.join( self.channel_ops[ chan ] ) ) )
				return
		
		if cmd == 'help':
			self.privmsg( target, '!help: this help text' )
		elif admin and cmd == 'admin_help':
			self.notice( source, '!die:                                   kill the bot' )
			self.notice( source, '!raw:                                   send raw irc command' )
			self.notice( source, '!admins:                                see who are admin' )
			self.notice( source, '!restart_class:                         restart the main Bot class' )
			self.notice( source, '!available_modules:                     see modules that are not currently loaded' )
			self.notice( source, '!enable_module <module>[ <module>...]:  enable one or more modules' )
			self.notice( source, '!disable_module <module>[ <module>...]: disable one or more modules' )

		for module_name, module in self.modules.items():
			try:
				if cmd == 'help' or module.can_handle( cmd, admin ):
					lines = module.handle( self, cmd, args, source, target, admin )
					if lines:
						for line in lines:
							c.notice( target, line )
			except Exception, e:
				print( "Module '{0}' handle error: {1}".format( module_name, e ) )

	def on_privmsg( self, c, e ):
		print( "on_privmsg" )
		self.__module_handle( 'privmsg', e )
		self.__process_command( c, e )

	def on_pubmsg( self, c, e ):
		print( "on_pubmsg" )
		self.__module_handle( 'privmsg', e )
		self.__process_command( c, e )
