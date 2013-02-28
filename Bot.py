from __future__ import print_function
import ConfigParser, sys, os, signal, subprocess
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_uh, is_channel
import modules

class Bot( SingleServerIRCBot ):
	"""The main brain of the IRC bot."""
	def __init__( self ):
		self.config = ConfigParser.SafeConfigParser()
		self.__reload_config()

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

		password = self.config.get( "main", "password" )

		channel = self.config.get( 'main', 'channel' )
		nickname = self.config.get( 'main', 'nickname' )

		if password != None:
			SingleServerIRCBot.__init__( self, [( server, port, password )], nickname, nickname )
		else:
			SingleServerIRCBot.__init__( self, [( server, port )], nickname, nickname )
		self.channel = channel
		self.admin = self.config.get( 'main', 'admin' ).split( ';' )
		self.load_modules()
		#self.bot = MyLovelyIRCBot( config.get( "main", "channel" ), config.get( "main", "nickname" ), server, port, password )
		#self.bot.set_admin( config.get( "main", "admin" ) )
		#for module in modules.getmodules():
	#		self.bot.add_module( modules.getmodule( module )( config.items( module ) ) )
		signal.signal( signal.SIGINT, self.sigint_handler )

	def __reload_config( self ):
		self.config.read( os.path.expanduser( "~/.ircbot" ) )
		
	def load_modules( self, reload = False ):
		"""Find and load all modules.
		Arguments:
		reload: force reload of config and modules
		"""
		if reload:
			self.__reload_config()
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
		self.modules[ module ] = modules.getmodule( module )( cfg )

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

#	def on_join( self, c, e ):
#		print( "on_join {0}, {1}".format( e.target(), e.source() ) )

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
		
		# nick is the sender of the message, target is either a channel or the sender.
		nick = nm_to_n( e.source() )
		target = e.target()
		if not is_channel( target ):
			target = nick
		
		# see if there is a module that is willing to handle this, and make it so.
		print( '__process_command (src: {0}; tgt: {1}; cmd: {2}; args: {3}; admin: {4})'.format( nick, target, cmd, args, admin ) )
		
		# handle die outside of module (in case module is dead :( )
		if admin and cmd == 'die':
			self.notice( source, 'Goodbye cruel world!' )
			self.die()
			return
		
		for module_name, module in self.modules.items():
			if module.can_handle( cmd, admin ):
				try:
					lines = module.handle( self, cmd, args, nick, target, admin )
					if lines:
						for line in lines:
							c.notice( target, line )
				except Exception, e:
					print( "Module '{0}' handle error: {1}".format( module_name, e ) )
				return

	def on_privmsg( self, c, e ):
		print( "on_privmsg" )
		self.__process_command( c, e )

	def on_pubmsg( self, c, e ):
		print( "on_pubmsg" )
		self.__process_command( c, e )