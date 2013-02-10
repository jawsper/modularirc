from __future__ import print_function
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, nm_to_uh, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import subprocess

class MyLovelyIRCBot( SingleServerIRCBot ):
	modules = []
	shutup = False
	
	def __init__( self, channel, nickname, server, port=6667, password=None ):
		if password != None:
			SingleServerIRCBot.__init__( self, [( server, port, password )], nickname, nickname )
		else:
			SingleServerIRCBot.__init__( self, [( server, port )], nickname, nickname )
		self.channel = channel
	
	def add_module( self, module ):
		self.modules.append( module )
	
	def set_admin( self, admin ):
		self.admin = admin

	def on_nicknameinuse( self, c, e ):
		print( "on_nicknameinuse" )
		c.nick( c.get_nickname() + "_" )

	def on_welcome( self, c, e ):
		print( "on_welcome" )
		c.join( self.channel )
	
	def on_join( self, c, e ):
		print( "on_join {0}, {1}".format( e.target(), e.source() ) )
		#if e.target() != "#" and nm_to_n( e.source() ) == c.get_nickname():
		#	c.notice( e.target(), "I am alive! Muhahaha!" )
		
	def on_disconnect( self, c, e ):
		print( "on_disconnect" )
		

	def on_privmsg( self, c, e ):
		print( "on_privmsg" )
		self.do_command( e, e.arguments()[0], nm_to_uh( e.source() ) == self.admin )

	def on_pubmsg( self, c, e ):
		print( "on_pubmsg" )
		if e.arguments()[0][0] == '!':
			self.do_command( e, e.arguments()[0][1:], nm_to_uh( e.source() ) == self.admin, False )
		a = e.arguments()[0].split(":", 1)
		if len(a) > 1 and irc_lower( a[0] ) == irc_lower( self.connection.get_nickname() ):
			self.do_command( e, a[1].strip(), nm_to_uh( e.source() ) == self.admin )
			return
		return

#	def on_dccmsg( self, c, e ):
#		print( "on_dccmsg" )
#		c.privmsg("You said: " + e.arguments()[0])
#
#	def on_dccchat( self, c, e ):
#		print( "on_dccchat" )
#		if len( e.arguments() ) != 2:
#			return
#		args = e.arguments()[1].split()
#		if len( args ) == 4:
#			try:
#				address = ip_numstr_to_quad( args[2] )
#				port = int( args[3] )
#			except ValueError:
#				return
#			self.dcc_connect( address, port )

	def do_command( self, e, args, admin = False, display_error = True ):
#		print e.source()
#		print e.target()
#		print e.arguments()
		args = args.split()
		cmd = args.pop(0).strip()
		self.dodo_command( e.source(), e.target(), cmd, args, admin, display_error )
		
	def dodo_command( self, source, target, cmd, args, admin = False, display_error = True ):
		nick = nm_to_n( source )
		c = self.connection
		print( "do_command (src: {0}; tgt: {1}; cmd: {2}; args: {3})".format( source, target, cmd, args ) )
		if admin:
			if not self.shutup:
			#	c.notice( nick, "Hiya boss!" )
				self.shutup = True
			
			if cmd == "die":
				c.notice( nick, "Goodbye cruel world!" )
				self.die()
				return
			#elif cmd == "shutup":
			#	c.notice( nick, "Sorry to bother you boss! :(" )
			#	self.shutup = True
			#	return
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
				c.notice( nick, "Doing %s to UT" % args[0] )
				r = subprocess.check_output( [ os.path.expanduser( '~/bin/ut-server' ), args[0] ] )
				c.notice( nick, "Result: %s" % r )
				return
			#elif cmd == "dcc":
			#	dcc = self.dcc_listen()
			#	c.ctcp( "DCC", nick, "CHAT chat %s %d" % ( ip_quad_to_numstr( dcc.localaddress ), dcc.localport ) )
			#else:
			#	c.notice( nick, "Not understood: " + cmd )
		#else:
		handled = False
		for module in self.modules:
			if module.handle_cmd( cmd ):
				handled = True
#				try:
				for line in module.handle( cmd, args, nick, admin ):
					c.notice( target, line )
#				except:
#					c.notice( target, "A module borked..." )
				break
		if cmd == "potato":
			c.notice( target, "I do quite enjoy potatoes" )
		elif cmd == "open" and " ".join( args ) == "the pod bay doors":
			c.notice( target, "I'm sorry, %s. I'm afraid I can't do that." % nm_to_n( source ) )
		elif display_error:
			c.notice( target, "Not understood: " + cmd )
