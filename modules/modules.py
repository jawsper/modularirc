from ._module import _module

class modules( _module ):
	def __init__( self, mgr ):
		_module.__init__( self, mgr, admin_only = True )

	def admin_cmd_modules( self, args, source, target, admin ):
		"""!modules: get all modules"""
		if not admin: return
		return [ 'Modules: {0}'.format( ', '.join( self.mgr.get_modules() ) ) ]

	def admin_cmd_available_modules( self, args, source, target, admin ):
		"""!available_modules: see modules that are not currently loaded"""
		if not admin: return
		return [ 'Available modules: ' + ', '.join( self.mgr.get_available_modules() ) ]

	def admin_cmd_reload_module( self, args, source, target, admin ):
		"""!reload_module <module>[ <module>...]: reload one or more modules"""
		if not admin: return
		return [ self.mgr.reload_module( m ) for m in args ]

	def admin_cmd_reload_modules( self, args, source, target, admin ):
		"""!reload_modules: reload all modules"""
		if not admin: return
		self.mgr.reload_modules()
		return [ 'Reloaded all modules' ]

	def admin_cmd_enable_module( self, args, source, target, admin ):
		"""!enable_module <module>[ <module>...]: enable one or more modules"""
		if not admin: return
		return [ self.mgr.enable_module( m ) for m in args ]
	def admin_cmd_disable_module( self, args, source, target, admin ):
		"""!disable_module <module>[ <module>...]: disable one or more modules"""
		if not admin: return
		return [ self.mgr.disable_module( m ) for m in args ]
