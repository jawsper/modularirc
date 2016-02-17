import pkgutil, os, sys
from imp import reload
import logging

def get_modules():
	"""Returns all modules that are found in the current package.
	Excludes modules starting with '_'"""
	return [ name for _,name, _ in pkgutil.iter_modules( [ os.path.dirname( __file__ ) ] ) if name[0] != '_' ]

def get_module( module ):
	"""Import module <module> and return the class.
	This returns the class modules.<module>.<module>"""
	mod = __import__( 'modules.{0}'.format( module ), fromlist = [ module ] )
	return getattr( mod, module )

def reload_module( module ):
	"""Reload a module given the module name. 
	This should be just the name, not the full module path.
	
	Arguments:
	module: the name of the module
	"""
	try:
		reload( getattr( sys.modules[ __name__ ], module ) )
	except AttributeError:
		pass

class ModuleLoadException( Exception ):
	pass

class Module(object):
	def __init__(self, manager, has_commands=True, admin_only=False):
		self.mgr = manager
		self.has_commands = has_commands
		self.admin_only = admin_only
		logging.info('Module {0} __init__'.format(self.__class__.__name__))
		self.start()
	def __del__(self):
		logging.info('Module {0} __del__'.format(self.__class__.__name__))
		self.stop()

	def start(self):
		pass
	def stop(self):
		pass

	def get_cmd_list(self, prefix='cmd_'):
		return ['!{0}'.format(cmd[len(prefix):]) for cmd in dir(self) if cmd.startswith(prefix)]
	def has_cmd(self, cmd, prefix='cmd_'):
		return hasattr(self, '{}{}'.format(prefix, cmd))
	def get_cmd( self, cmd, prefix='cmd_'):
		return getattr(self, '{}{}'.format(prefix, cmd))

	def get_admin_cmd_list(self):
		return self.get_cmd_list(prefix='admin_cmd_')
	def has_admin_cmd(self, cmd):
		return self.has_cmd(cmd, prefix='admin_cmd_')
	def get_admin_cmd(self, cmd):
		return self.get_cmd(cmd, prefix='admin_cmd_')

	# methods that directly call the mgr

	def notice(self, target, message):
		self.mgr.notice(target, message)
	def privmsg(self, target, message):
		self.mgr.privmsg(target, message)

	def get_config(self, key, default=None):
		return self.mgr.get_config(self.__class__.__name__, key, default)
	def set_config(self, key, value):
		self.mgr.set_config(self.__class__.__name__, key, value)

	def get_module(self, name):
		return self.mgr.get_module(name)
