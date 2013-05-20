class _module(object):
	def __init__( self, manager ):
		self.mgr = manager
		print( 'Loading module {0}'.format( self.__class__.__name__ ) )
	def stop(self):
		pass
	def can_handle( self, cmd, admin ):
		return False
	def handle( self, cmd, args, source, target, admin ):
		pass
		
	# methods that directly call the mgr

	def notice( self, target, message ):
		self.mgr.notice( target, message )
	def privmsg( self, target, message ):
		self.mgr.privmsg( target, message )
		
	def get_config( self, key ):
		return self.mgr.get_config( self.__class__.__name__, key )
	def set_config( self, key, value ):
		self.mgr.set_config( self.__class__.__name__, key, value )
