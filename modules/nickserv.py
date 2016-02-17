from modules import Module

class nickserv(Module):
	"""nickserv: automatically auth with nickserv"""
	def __init__(self, mgr):
		super().__init__(mgr, admin_only=True)

	def on_welcome(self, connection, event):
		if self.get_config( 'password', False ):
			self.privmsg( 'NickServ', 'IDENTIFY ' + self.get_config( 'password' ) )

	def admin_cmd_nickserv_auth( self, args, source, target, admin ):
		if not admin: return
		if not self.get_config( 'password', False ):
			self.notice( source, 'Password not set' )
		self.notice( source, 'Sending IDENTIFY message to NickServ' )
		self.privmsg( 'NickServ', 'IDENTIFY ' + self.get_config( 'password' ) )
