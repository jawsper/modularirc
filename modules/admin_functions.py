from _module import _module
import os, subprocess

class admin_functions( _module ):
	def __handler( self, cmd ):
		return '_admin_functions__handle_' + cmd

	def can_handle( self, cmd, admin ):
		return admin and hasattr( self, self.__handler( cmd ) ) or cmd in ( '+o', '-o' )

	def handle( self, cmd, args, source, target, admin ):
		if not admin:
			return
		if hasattr( self, self.__handler( cmd ) ):
			getattr( self, self.__handler( cmd ) )( cmd, args, source, target, admin )
		if cmd in ( '+o', '-o' ):
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
						bot.connection.mode( dest, cmd + " " + nick )
			elif len( args ) == 1 and args[0][0] == '#':
				self.mgr.bot.connection.mode( args[0], cmd + " " + source )
			elif target[0] == '#':
				self.mgr.bot.connection.mode( target, cmd + " " + source )
			else:
				self.notice( source, "Usage: <+|->o <#<channel>|nicknames>" )


	# command handlers
	
	# !admin_help handler
	def __handle_admin_help( self, cmd, args, source, target, admin ):
		if admin:
			for msg in (
				'!update_source: updates the source of the bot. does not reload the bot or the modules',
				'!say <target> <message>: make the bot speak',
				'!notice <target> <message>: make the bot send a notice',
				'!modules: show loaded modules',
				'!reload_modules: reload modules',
				'!stats: show statistics',
				'!nick <nick>: change the nick',
				'!join <channel>[ <channel>...]: join a channel',
				'!part [<channel>]: part this or a specific channel',
				'!+o <args>: make someone op',
				'!-o <args>: make someone not op',
			):
				self.notice( source, msg )
	# handle update git
	def __handle_update_source( self, cmd, args, source, target, admin ):
		self.mgr.notice( source, 'Please wait, running git...' )
		result = subprocess.Popen( [ 'git', 'pull' ], stdout = subprocess.PIPE, cwd = os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) ) ).communicate()[0]
		self.notice( source, 'Result: ' + result )
	# make the bot speak
	def __handle_say( self, *args ):
		self.__handle_privmsg( *args )
	def __handle_privmsg( self, cmd, args, source, target, admin ):
		self.privmsg( args.pop(0), ' '.join( args ) )
	def __handle_notice( self, cmd, args, source, target, admin ):
		self.notice( args.pop(0), ' '.join( args ) )

	# show loaded modules
	def __handle_modules( self, cmd, args, source, target, admin ):
		self.notice( target, 'Loaded modules: ' + ' '.join( sorted( bot.modules ) ) )
	# reload all the modules
#	def __handle_reload_modules( self, cmd, args, source, target, admin ):
#		self.mgr.load_modules( reload = True )

	# show bot statistics
	def __handle_stats( self, cmd, args, source, target, admin ):
		for chname, chobj in self.mgr.bot.channels.items():
			self.notice( source, "--- Channel statistics ---" )
			self.notice( source, "Channel: " + chname )
			users = chobj.users()
			users.sort()
			self.notice( source, "Users: " + ", ".join( users ) )
			opers = chobj.opers()
			opers.sort()
			self.notice( source, "Opers: " + ", ".join( opers ) )
			voiced = chobj.voiced()
			voiced.sort()
			self.notice( source, "Voiced: " + ", ".join( voiced ) )

	# change bot nick
	def __handle_nick( self, cmd, args, source, target, admin ):
		self.mgr.bot.connection.nick( args[0] )

	# make bot join channel(s)
	def __handle_join( self, cmd, args, source, target, admin ):
		for channel in args:
			self.mgr.bot.connection.join( channel )

	# make bot leave channel(s)
	def __handle_part( self, cmd, args, source, target, admin ):
		if len( args ) > 0:
			self.mgr.bot.connection.part( args )
		elif target[0] == '#':
			self.mgr.bot.connection.part( target )
