import importlib
import os
import pkgutil
import sys

MODULES_ROOT = os.path.dirname(__file__)

def list_modules(root=MODULES_ROOT):
    load_dirs = []
    for entry in [os.path.join(root, item) for item in os.listdir(root) if item[0] != '_']:
        if not os.path.isdir(entry):
            continue
        if not os.path.isfile(os.path.join(entry, '__init__.py')):
            continue
        load_dirs.append(entry)

    return [module_info for module_info in pkgutil.iter_modules(load_dirs) if module_info.name[0] != '_']

def load_module(module_info):
    module_spec = module_info.module_finder.find_spec(module_info.name)
    module = module_spec.loader.load_module()
    return module

def reload_module(module_info):
    """Reloads a Python module, by the module_info given.
    """
    # first insert module path into path, otherwise reload on Python 3.4+ can't find it
    sys.path.insert(1, module_info.module_finder.path)
    module = importlib.reload(sys.modules[module_info.name])
    del sys.path[1]
    return module
