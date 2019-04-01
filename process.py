from __future__ import print_function

import os
import subprocess

import env
import config
from util import clear_screen, is_string, string_to_args

DEFAULT_CONFIRM = 'Press Enter to continue...'

class Command(object):

    def __init__(self, config):
        self.config = config
        self.taskrc_path = os.path.expanduser(self.config.get('taskwarrior', 'taskrc'))
        self.env = env.user
        self.env['TASKRC'] = self.taskrc_path

    def run(self, command, capture_output=False):
        if is_string(command):
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
        return proc.returncode, stdout, stderr

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
        return output


