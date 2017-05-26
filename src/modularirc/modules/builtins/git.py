import os
import subprocess

from modularirc import BaseModule


class Module(BaseModule):
    # handle update git
    def __get_base_path(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def admin_cmd_update_source(self, source, **kwargs):
        """!update_source: updates the source of the bot. does not reload the bot or the modules"""
        self.notice(source, 'Please wait, running git...')
        result = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE, cwd=self.__get_base_path()).communicate()[0]
        return ['Result: ' + result.decode('utf-8')]

    def cmd_git(self, args, **kwargs):
        """!git log [skip]: shows git commit"""
        if len(args) == 0:
            return [self.cmd_git.__doc__]
        if args[0] == 'log':
            try:
                skip = int(args[1])
            except:
                skip = 0
            result = subprocess.Popen(['git', 'log', '-n1', '--skip='+str(skip)], stdout=subprocess.PIPE, cwd=self.__get_base_path()).communicate()[0]
            return result.decode('utf-8').split('\n')
