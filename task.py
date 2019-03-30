from __future__ import print_function

import os
import subprocess
import shlex
from tasklib import TaskWarrior

import env
import config
from util import clear_screen, is_string

DEFAULT_TASKRC = '~/.taskrc'
DEFAULT_CONFIRM = 'Press Enter to continue...'

class TaskCommand(object):

    def __init__(self):
        self.taskrc_path = os.path.expanduser(hasattr(config, 'TASKRC') and config.TASKRC or DEFAULT_TASKRC)
        self.env = env.user
        self.env['TASKRC'] = self.taskrc_path

    def run(self, command):
        if is_string(command):
            command = shlex.split(command)
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=self.env,
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr

    def result(self, command, confirm=DEFAULT_CONFIRM, clear=True):
        if clear:
            clear_screen()
        returncode, stdout, stderr = self.run(command)
        output = returncode == 0 and stdout or stderr
        print(output)
        if confirm:
            try:
                input(confirm)
            except:
                raw_input(confirm)
        if clear:
            clear_screen()

class TaskModel(object):
    def __init__(self, task_config, reports, report=None, data_location=None):

        if not data_location:
            data_location = task_config.subtree('data.location', walk_subtree=True)
        self.data_location = os.path.expanduser(data_location)
        self.tw = TaskWarrior(self.data_location)
        self.reports = reports
        self.report = report
        self.tasks = []
        if report:
            self.update_report(report)

    def add(self, contact):
        pass

    def active_report(self):
        return self.reports[self.report]

    def update_report(self, report):
        self.report = report
        self.tasks = self.tw.tasks.filter(*self.active_report()['filter'])

#    def get_summary(self, report=None):
#        report = report or self.report
#        self.update_report(report)
#        summary = []
#        for task in self.tasks:
#            summary.append(self.build_task_row(task))
#        return summary
#
#    def _reload_list(self, new_value=None):
#        self._list_view.options = self._model.get_summary()
#        self._list_view.value = new_value


