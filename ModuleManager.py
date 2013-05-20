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
			try:
				self.loaded_modules[ module_name ].stop()
			except Exception as e:
				pass
			del self.loaded_modules[ module_name ]
		del self.modules[ module_name ]
		return 'Module removed'
			
	def enable_module( self, module_name ):
		pass
	def disable_module( self, module_name ):
		pass
	def reload_module( self, module_name ):
		pass
