from modularirc import BaseModule


class Module(BaseModule):
    def __init__(self, mgr):
        super().__init__(mgr, admin_only=True)

    def admin_cmd_modules(self, admin, **kwargs):
        """!modules: get all modules"""
        if not admin: return
        return ['Modules: {0}'.format(', '.join(self.mgr.get_modules()))]

    def admin_cmd_available_modules(self, admin, **kwargs):
        """!available_modules: see modules that are not currently loaded"""
        if not admin: return
        return ['Available modules: {}'.format(', '.join(self.mgr.get_available_modules()))]

    def admin_cmd_reload_module(self, arglist, admin, **kwargs):
        """!reload_module <module>[ <module>...]: reload one or more modules"""
        if not admin: return
        return [self.mgr.reload_module(m) for m in arglist]

    def admin_cmd_reload_modules(self, admin, **kwargs):
        """!reload_modules: reload all modules"""
        if not admin: return
        self.mgr.reload_modules()
        return ['Reloaded all modules']

    def admin_cmd_enable_module(self, arglist, admin, **kwargs):
        """!enable_module <module>[ <module>...]: enable one or more modules"""
        if not admin: return
        return [self.mgr.enable_module(m) for m in arglist]

    def admin_cmd_disable_module(self, arglist, admin, **kwargs):
        """!disable_module <module>[ <module>...]: disable one or more modules"""
        if not admin: return
        return [self.mgr.disable_module(m) for m in arglist]
