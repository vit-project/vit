import os
import re
import subprocess
import copy

from vit import env
from vit.util import clear_screen, string_to_args

DEFAULT_CONFIRM = 'Press Enter to continue...'

class Command:

    def __init__(self, config):
        self.config = config
        self.env = env.user.copy()
        self.env['TASKRC'] = self.config.taskrc_path

    def run(self, command, capture_output=False, custom_env={}):
        if isinstance(command, str):
            command = string_to_args(command)
        env = copy.copy(self.env)
        env.update(custom_env)
        kwargs = {
            'env': env,
        }
        if capture_output:
            kwargs.update({
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'universal_newlines': True,
            })
        try:
            proc = subprocess.Popen(command, **kwargs)
            stdout, stderr = proc.communicate()
            returncode = proc.returncode
        except Exception as e:
            stdout = ''
            stderr = e.message if hasattr(e, 'message') else str(e)
            returncode = 1
        return returncode, stdout, self.filter_errors(returncode, stderr)

    def result(self, command, confirm=DEFAULT_CONFIRM, capture_output=False, print_output=False, clear=True, custom_env={}):
        if clear:
            clear_screen()
        returncode, stdout, stderr = self.run(command, capture_output, custom_env)
        output = returncode == 0 and stdout or stderr
        if print_output:
            print(output)
        if confirm:
            try:
                input(confirm)
            except:
                raw_input(confirm)
        if clear:
            clear_screen()
        return returncode, output

    def filter_errors(self, returncode, error_string):
        if not error_string:
            return '' if returncode == 0 else 'unknown'
        regex = '(TASKRC override)|(^$)'
        filtered_lines = list(filter(lambda s: False if len(re.findall(regex, s)) else True, error_string.split("\n")))
        return "\n".join(filtered_lines)
