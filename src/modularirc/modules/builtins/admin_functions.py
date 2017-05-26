from modularirc import BaseModule


class Module(BaseModule):
    """admin_functions: special functions for admins"""
    
    def __init__(self, mgr):
        super().__init__(mgr, admin_only=True)

    #def handle( self, cmd, args, source, target, admin ):
    #   if not admin:
    #       return
    #   if cmd in ( '+o', '-o' ):
    #       if len( args ) > 1:
    #           dest = None
    #           nicks = None
    #           if args[0][0] == '#':
    #               dest = args[0]
    #               nicks = args[1:]
    #           elif target[0] == '#':
    #               dest = target
    #               nicks = args
    #           if dest != None:
    #               for nick in nicks:
    #                   self.mgr.bot.connection.mode( dest, cmd + " " + nick )
    #       elif len( args ) == 1 and args[0][0] == '#':
    #           self.mgr.bot.connection.mode( args[0], cmd + " " + source )
    #       elif target[0] == '#':
    #           self.mgr.bot.connection.mode( target, cmd + " " + source )
    #       else:
    #           self.notice( source, "Usage: <+|->o <#<channel>|nicknames>" )


    # command handlers
    
    # !admin_help handler
    #def admin_cmd_admin_help( self, args, source, target, admin ):
    #   if admin:
    #       for msg in (
    #           '!modules: show loaded modules',
    #           '!reload_modules: reload modules',
    #           '!+o <args>: make someone op',
    #           '!-o <args>: make someone not op',
    #       ):
    #           self.notice( source, msg )
    
    def admin_cmd_op(self, arglist, source, target, **kwargs):
        """!op <+o|-o> <args>: make or break someone as op"""
        if len(arglist) == 0:
            return [self.admin_cmd_op.__doc__]
        cmd = arglist[ 0 ]
        args = arglist[ 1: ]
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
                        self.mgr.bot.connection.mode( dest, cmd + ' ' + nick )
            elif len( args ) == 1 and args[0][0] == '#':
                self.mgr.bot.connection.mode( args[0], cmd + ' ' + source )
            elif target[0] == '#':
                self.mgr.bot.connection.mode( target, cmd + ' ' + source )
            else:
                self.notice( source, "Usage: !op <+|->o [<#<channel>|nicknames>]" )

    # make the bot speak
    def admin_cmd_say(self, arglist, **kwargs):
        """!say <target> <message>: make the bot speak"""
        self.privmsg(arglist[0], ' '.join(arglist[1:]))
    def admin_cmd_notice(self, arglist, **kwargs):
        """!notice <target> <message>: make the bot send a notice"""
        self.notice(arglist[0], ' '.join(arglist[1:]))

    # show bot statistics
    def admin_cmd_stats(self, **kwargs):
        """!stats: show statistics"""
        stats = []
        for chname, chobj in list(self.mgr.bot.channels.items()):
            stats.append( "--- Channel statistics ---" )
            stats.append( "Channel: " + chname )
            users = chobj.users()
            users.sort()
            stats.append( "Users: " + ", ".join( users ) )
            opers = chobj.opers()
            opers.sort()
            stats.append( "Opers: " + ", ".join( opers ) )
            voiced = chobj.voiced()
            voiced.sort()
            stats.append( "Voiced: " + ", ".join( voiced ) )
        return stats

    # change bot nick
    def admin_cmd_nick(self, arglist, **kwargs):
        """!nick <nick>: change the nick"""
        self.mgr.bot.connection.nick(arglist[0])

    # make bot join channel(s)
    def admin_cmd_join(self, arglist, **kwargs):
        """!join <channel>[ <channel>...]: join a channel"""
        for channel in arglist:
            self.mgr.bot.connection.join(channel)

    # make bot leave channel(s)
    def admin_cmd_part(self, arglist, target, **kwargs):
        """!part [<channel>]: part this or a specific channel"""
        if len(arglist) > 0:
            self.mgr.bot.connection.part(arglist)
        elif target[0] == '#':
            self.mgr.bot.connection.part(target)
