class _module(object):
	def __init__( self, manager ):
		self.mgr = manager
	def stop(self):
		pass
	def can_handle( self, cmd, admin ):
		return False
	def handle( self, cmd, args, source, target, admin ):
		pass

	def notice( self, target, message ):
		self.mgr.notice( target, message )
	def privmsg( self, target, message ):
		self.mgr.privmsg( target, message )
