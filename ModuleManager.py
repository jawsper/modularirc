import modules

class ModuleManager( object ):
	def __init__( self, bot ):
		self.bot = bot
		self.modules = {}
		self.loaded_modules = {}
	
	def add_module( self, module_name ):
		if module_name in self.modules:
			return 'Module already available'
		try:
			module = modules.getmodule( module_name )
			if module:
				self.modules[ module_name ] = module
				return
		except Exception as e:
			return str( e )
		return 'Module not available'

	def remove_module( self, module_name ):
		if not module_name in self.modules:
			return 'Module not available'
		if module_name in self.loaded_modules:
			self.disable_module( module_name )
		del self.modules[ module_name ]
		return 'Module removed'
			
	def enable_module( self, module_name ):
		if not module_name in self.modules:
			return 'Module not available'
		if module_name in self.loaded_modules:
			return 'Module already enabled'
		try:
			self.loaded_modules[ module_name ] = self.modules[ module_name ]( self )
		except Exception as e:
			return 'Module failed to load: {0}'.format( e )
		return 'Module enabled'

	def disable_module( self, module_name ):
		if not module_name in self.loaded_modules:
			return 'Module not enabled'
		try:
			self.loaded_modules[ module_name ].stop()
		except Exception as e:
			pass
		del self.loaded_modules[ module_name ]
		return 'Module disabled'

	def reload_module( self, module_name ):
		if not module_name in self.modules:
			return 'Module not available'
		if module_name in self.loaded_modules:
			self.disable_module( module_name )
		self.enable_module( module_name )
		return 'Module reloaded'

