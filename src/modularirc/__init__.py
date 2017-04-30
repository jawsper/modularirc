__author__ = 'Jasper Seidel <code@jawsper.nl>'
__version__ = '0.1.0'

from .module_manager import BaseModule


class BotRestartException(Exception):
    pass


class BotReloadException(Exception):
    pass


class BotExitException(Exception):
    pass
