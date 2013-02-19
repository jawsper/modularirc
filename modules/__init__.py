import pkgutil, os

def getmodules():
	return [ name for _,name, _ in pkgutil.iter_modules( [ os.path.dirname( __file__ ) ] ) ]

def getmodule( module ):
	mod = __import__( 'modules.{0}'.format( module ), fromlist = [ module ] )
	return getattr( mod, module )