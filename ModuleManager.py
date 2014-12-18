import modules
import logging

class ModuleManager( object ):
	def __init__( self, bot ):
		self.bot = bot
		self.modules = {}
		self.loaded_modules = {}
		for module_name in modules.get_modules():
			logging.info( 'Loading module {0}: {1}'.format( module_name, self.add_module( module_name ) ) )

	def unload( self ):
		for module_name in list( self.modules.keys() ):
			logging.info( 'Unloading module {0}: {1}'.format( module_name, self.remove_module( module_name ) ) )

	def reload_modules( self ):
		"""Reload all modules. Warning: this is fairly destructive"""
		# remove modules that no longer exist
		for module_name in [ m for m in self.modules.keys() if m not in modules.get_modules() ]:
			self.remove_module( module_name )
		# reload all modules
		for module_name in self.modules:
			self.reload_module( module_name )
		# add modules that are not added yet
		for module_name in [ m for m in modules.get_modules() if m not in self.modules ]:
			self.add_module( module_name )

	def get_modules( self ):
		"""Get all found modules"""
		return iter( self.modules.keys() )

	def get_loaded_modules( self ):
		"""Get all loaded modules"""
		return list( self.loaded_modules.items() )
		
	def module_is_loaded( self, module_name ):
		return module_name in self.loaded_modules
	def get_module( self, module_name ):
		try:
			return self.loaded_modules[ module_name ]
		except:
			return False

	def get_available_modules( self ):
		"""Get all available modules: modules that are found but not loaded"""
		modules = [ key for key in self.modules.keys() if key not in self.loaded_modules ]
		modules.sort()
		return modules
	
	def add_module( self, module_name ):
		"""Load a module"""
		if module_name in self.modules:
			return 'Module already available'
		try:
			module = modules.get_module( module_name )
			if module:
				self.modules[ module_name ] = module
				return 'Module added'
		except Exception as e:
			return 'Error loading module: {0}'.format( e )
		return 'Module not available'

	def remove_module( self, module_name ):
		"""Unload a module"""
		if not module_name in self.modules:
			return 'Module not available'
		if module_name in self.loaded_modules:
			self.disable_module( module_name )
		del self.modules[ module_name ]
		return 'Module removed'
			
	def enable_module( self, module_name ):
		"""Enable a module"""
		if not module_name in self.modules:
			return 'Module {} not available'.format( module_name )
		if module_name in self.loaded_modules:
			return 'Module {} already enabled'.format( module_name )
		try:
			self.loaded_modules[ module_name ] = self.modules[ module_name ]( self )
		except Exception as e:
			return 'Module {} failed to load: {}'.format( module_name, e )
		return 'Module {} enabled'.format( module_name )

	def disable_module( self, module_name ):
		"""Disable a module"""
		if not module_name in self.loaded_modules:
			return 'Module not enabled'
		try:
			self.loaded_modules[ module_name ].stop()
		except Exception as e:
			logger.warning( 'Module %s failed to stop: %s', module_name, e )
		del self.loaded_modules[ module_name ]
		return 'Module {} disabled'.format( module_name )

	def restart_module( self, module_name ):
		"""Restart a module"""
		if not module_name in self.modules:
			return 'Module {} not available'.format( module_name )
		if module_name in self.loaded_modules:
			self.disable_module( module_name )
		self.enable_module( module_name )
		return 'Module {} restarted'.format( module_name )
	
	def reload_module( self, module_name ):
		"""Reload a module"""
		start_module = module_name in self.loaded_modules
		self.remove_module( module_name ) # remove to clear references
		modules.reload_module( module_name ) # actually reload class
		self.add_module( module_name ) # re-add module
		if start_module: # enable if it was enabled
			self.enable_module( module_name )
		return 'Module {} reloaded'.format( module_name )

	# methods from Bot
	
	def notice( self, target, message ):
		self.bot.notice( target, message )
	
	def privmsg( self, target, message ):
		self.bot.privmsg( target, message )

	def get_config( self, group, key, default = None ):
		return self.bot.get_config( group, key, default )

	def set_config( self, group, key, value ):
		return self.bot.set_config( group, key, value )

	def get_module(self, name):
		if name in self.loaded_modules:
			return self.loaded_modules[name]
