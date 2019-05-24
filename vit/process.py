from __future__ import print_function
from future.utils import string_types

import os
import re
import subprocess

from vit import env
from vit.util import clear_screen, string_to_args

DEFAULT_CONFIRM = 'Press Enter to continue...'

class Command(object):

    def __init__(self, config):
        self.config = config
        self.taskrc_path = os.path.expanduser(self.config.get('taskwarrior', 'taskrc'))
        self.env = env.user
        self.env['TASKRC'] = self.taskrc_path

    def run(self, command, capture_output=False):
        if isinstance(command, string_types):
            command = string_to_args(command)
        kwargs = {
            'env': self.env,
        }
        if capture_output:
            kwargs.update({
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'universal_newlines': True,
            })
        proc = subprocess.Popen(command, **kwargs)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, self.filter_errors(stderr)

    def result(self, command, confirm=DEFAULT_CONFIRM, capture_output=False, print_output=False, clear=True):
        if clear:
            clear_screen()
        returncode, stdout, stderr = self.run(command, capture_output)
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

    def filter_errors(self, error_string):
        if not error_string:
            return ''
        regex = '(TASKRC override)|(^$)'
        filtered_lines = list(filter(lambda s: False if len(re.findall(regex, s)) else True, error_string.split("\n")))
        return "\n".join(filtered_lines)
