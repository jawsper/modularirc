from __future__ import print_function
import ConfigParser, sys, os, signal, subprocess
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_uh, is_channel
import modules

class Bot( SingleServerIRCBot ):
	def __init__( self ):
		self.config = ConfigParser.SafeConfigParser()
		self.config.read( os.path.expanduser( "~/.ircbot" ) )

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
		self.__load_modules()
		#self.bot = MyLovelyIRCBot( config.get( "main", "channel" ), config.get( "main", "nickname" ), server, port, password )
		#self.bot.set_admin( config.get( "main", "admin" ) )
		#for module in modules.getmodules():
	#		self.bot.add_module( modules.getmodule( module )( config.items( module ) ) )
		signal.signal( signal.SIGINT, self.sigint_handler )

	def __load_modules( self, reload = False ):
		self.modules = {}
		for module in modules.getmodules():
			self.__add_module( module, reload )
		
	def __add_module( self, module, reload = False ):
		if reload:
			modules.reload_module( module )
		try:
			cfg = self.config.items( module )
		except ConfigParser.NoSectionError:
			cfg = {}
		self.modules[ module ] = modules.getmodule( module )( cfg )

	def sigint_handler( self, signal, frame ):
		print( 'Ctrl+C pressed, shutting down!' )
		self.die()
		sys.exit(0)

	# from old bot

	def on_nicknameinuse( self, c, e ):
		print( "on_nicknameinuse" )
		c.nick( c.get_nickname() + "_" )

	def on_welcome( self, c, e ):
		print( "on_welcome" )
		c.join( self.channel )

#	def on_join( self, c, e ):
#		print( "on_join {0}, {1}".format( e.target(), e.source() ) )

#	def on_disconnect( self, c, e ):
#		print( "on_disconnect" )

	def __process_command( self, c, e ):
		message = e.arguments()[0]
		if message[0] != '!':
			return
		args = message[1:].split()
		cmd = args.pop(0).strip()
		admin = nm_to_uh( e.source() ) in self.admin
		nick = nm_to_n( e.source() )
		target = e.target()
		if not is_channel( target ):
			target = nick
		print( "__process_command (src: {0}; tgt: {1}; cmd: {2}; args: {3}; admin: {4})".format( nick, target, cmd, args, admin ) )
		if admin:
			if cmd == 'say': cmd = 'privmsg'
			if cmd == "die":
				c.notice( nick, "Goodbye cruel world!" )
				self.die()
				return
			elif cmd == 'privmsg' or cmd == 'action':
				getattr( c, cmd )( args[0], ' '.join( args[1:] ) )
				return
			elif cmd == 'reload_modules':
				self.__load_modules( reload = True )
			elif cmd == "stats":
				for chname, chobj in self.channels.items():
					c.notice( nick, "--- Channel statistics ---" )
					c.notice( nick, "Channel: " + chname )
					users = chobj.users()
					users.sort()
					c.notice( nick, "Users: " + ", ".join( users ) )
					opers = chobj.opers()
					opers.sort()
					c.notice( nick, "Opers: " + ", ".join( opers ) )
					voiced = chobj.voiced()
					voiced.sort()
					c.notice( nick, "Voiced: " + ", ".join( voiced ) )
				return
			elif cmd == 'nick':
				c.nick( args[0] )
				return
			elif cmd == "join":
				for channel in args:
					c.join( channel )
				return
			elif cmd == "part":
				if len( args ) > 0:
					c.part( args )
				elif target[0] == '#':
					c.part( [ target ] )
				return
			elif False and cmd == "+o":
				if target[0] == '#':
					c.mode( target, nick )
				return
			elif ( cmd == "+o" or cmd == "-o" ):
				if len( args ) > 1:
					dest = None
					nicks = None
					if args[0][0] == '#':
						dest = args[0]
						nicks = args[1:]
					elif target[0] == '#':
						dest = target
						nicks = args
					if dest != None:
						for nick in nicks:
							c.mode( dest, cmd + " " + nick )
				elif len( args ) == 1 and args[0][0] == '#':
					c.mode( args[0], cmd + " " + nick )
				elif target[0] == '#':
					c.mode( target, cmd + " " + nick )
				else:
					c.notice( nick, "Usage: <+|->o <#<channel>|nicknames>" )
				return
			elif cmd == "ut" and len( args ) == 1 and args[0] in ( 'start', 'stop' ):
				c.notice( nick, 'Doing {0} to UT'.format( args[0] ) )
				r = subprocess.check_output( [ os.path.expanduser( '~/bin/ut-server' ), args[0] ] )
				c.notice( nick, 'Result: {0}'.format( r ) )
				return
		for module_name, module in self.modules.items():
			if module.handle_cmd( cmd ):
#				try:
				for line in module.handle( cmd, args, nick, admin ):
					c.notice( target, line )
#				except:
#					c.notice( target, "A module borked..." )
				return
		if cmd == "potato":
			c.notice( target, "I do quite enjoy potatoes" )
		elif cmd == "open" and " ".join( args ) == "the pod bay doors":
			c.notice( target, "I'm sorry, {0}. I'm afraid I can't do that.".format( nick ) )
		#elif display_error:
		#	c.notice( target, "Not understood: " + cmd )

	def on_privmsg( self, c, e ):
		print( "on_privmsg" )
		self.__process_command( c, e )
		#self.do_command( e, e.arguments()[0], nm_to_uh( e.source() ) == self.admin )

	def on_pubmsg( self, c, e ):
		print( "on_pubmsg" )
		self.__process_command( c, e )