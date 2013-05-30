import pkgutil, os, sys

def getmodules():
	return get_modules()
def get_modules():
	"""Returns all modules that are found in the current package.
	Excludes modules starting with '_'"""
	return [ name for _,name, _ in pkgutil.iter_modules( [ os.path.dirname( __file__ ) ] ) if name[0] != '_' ]

def getmodule( module ):
	return get_module( module )
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