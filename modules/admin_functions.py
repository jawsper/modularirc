from _module import _module

class admin_functions( _module ):
	def __handler( self, cmd ):
		return '_admin_functions__handle_' + cmd

	def can_handle( self, cmd, admin ):
		return admin and hasattr( self, self.__handler( cmd ) ) or cmd in ( '+o', '-o' )

	def handle( self, bot, cmd, args, source, target, admin ):
		if hasattr( self, self.__handler( cmd ) ):
			getattr( self, self.__handler( cmd ) )( bot, cmd, args, source, target, admin )
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
				bot.connection.mode( args[0], cmd + " " + source )
			elif target[0] == '#':
				bot.connection.mode( target, cmd + " " + source )
			else:
				bot.notice( source, "Usage: <+|->o <#<channel>|nicknames>" )


	# command handlers
	
	# !admin_help handler
	def __handle_admin_help( self, bot, cmd, args, source, target, admin ):
		if admin:
			for msg in ( 
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
				bot.notice( source, msg )

	# make the bot speak
	def __handle_say( self, *args ):
		self.__handle_privmsg( *args )
	def __handle_privmsg( self, bot, cmd, args, source, target, admin ):
		bot.privmsg( args.pop(0), ' '.join( args ) )
	def __handle_notice( self, bot, cmd, args, source, target, admin ):
		bot.notice( args.pop(0), ' '.join( args ) )

	# show loaded modules
	def __handle_modules( self, bot, cmd, args, source, target, admin ):
		bot.notice( target, 'Loaded modules: ' + ' '.join( sorted( bot.modules ) ) )
	# reload all the modules
	def __handle_reload_modules( self, bot, cmd, args, source, target, admin ):
		bot.load_modules( reload = True )

	# show bot statistics
	def __handle_stats( self, bot, cmd, args, source, target, admin ):
		for chname, chobj in bot.channels.items():
			bot.notice( source, "--- Channel statistics ---" )
			bot.notice( source, "Channel: " + chname )
			users = chobj.users()
			users.sort()
			bot.notice( source, "Users: " + ", ".join( users ) )
			opers = chobj.opers()
			opers.sort()
			bot.notice( source, "Opers: " + ", ".join( opers ) )
			voiced = chobj.voiced()
			voiced.sort()
			bot.notice( source, "Voiced: " + ", ".join( voiced ) )

	# change bot nick
	def __handle_nick( self, bot, cmd, args, source, target, admin ):
		bot.connection.nick( args[0] )

	# make bot join channel(s)
	def __handle_join( self, bot, cmd, args, source, target, admin ):
		for channel in args:
			bot.connection.join( channel )

	# make bot leave channel(s)
	def __handle_part( self, bot, cmd, args, source, target, admin ):
		if len( args ) > 0:
			bot.connection.part( args )
		elif target[0] == '#':
			bot.connection.part( target )
