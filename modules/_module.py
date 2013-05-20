class _module(object):
	def __init__( self, manager ):
		self.mgr = manager
	def stop(self):
		pass
	def can_handle( self, cmd, admin ):
		return False
	def handle( self, bot, cmd, args, source, target, admin ):
		pass
