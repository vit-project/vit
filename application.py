#!/usr/bin/env python

import subprocess

import urwid

from util import clear_screen, string_to_args
from task import TaskCommand, TaskListModel
from report import TaskTable, SelectableRow, TaskListBox
import event
from command_bar import CommandBar

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

class Application():
    def __init__(self, task_config, reports, report):

        self.config = task_config
        self.reports = reports
        self.report = report
        self.command = TaskCommand()
        self.event = event.Emitter()
        self.event.listen('command-bar:keypress', self.command_bar_keypress)
        self.run(self.report)

    def command_bar_keypress(self, data):
        if data['key'] in ('enter'):
            args = string_to_args(data['text'])
            metadata = data['metadata']
            if metadata['op'] == 'add':
                self.execute_command(['task', 'add'] + args)
            if metadata['op'] == 'modify':
                # TODO: Will this break if user clicks another list item
                # before hitting enter?
                self.execute_command(['task', metadata['uuid'], 'modify'] + args)
        self.widget.focus_position = 'body'

    def key_pressed(self, key):
        if key in ('q', 'Q', 'esc'):
            raise urwid.ExitMainLoop()
        if key in ('u'):
            self.execute_command(['task', 'undo'])

    def on_select(self, row, size, key):
        if key in ('a'):
            self.footer.set_metadata({'op': 'add'})
            self.set_command_prompt('Add: ')
            return None
        if key in ('m'):
            if self.widget.focus_position == 'body':
                self.footer.set_metadata({'op': 'modify', 'uuid': self.widget.body.focus.uuid})
                self.set_command_prompt('Modify: ')
            return None
        if key in ('e'):
            self.execute_command(['task', row.uuid, 'edit'])
            return None
        elif key in ('enter'):
            self.execute_command(['task', row.uuid, 'info'], update_report=False)
            return None
        return key

    def build_report(self):
        self.model = TaskListModel(self.config, self.reports, self.report)
        self.table = TaskTable(self.config, self.reports[self.report], self.model.tasks, on_select=self.on_select)

        self.header = urwid.Pile([
            urwid.Text('Welcome to PYT'),
            self.table.header,
        ])
        self.footer = CommandBar(event=self.event)

    def execute_command(self, args, update_report=True):
        self.loop.stop()
        self.command.result(args)
        if update_report:
            self.update_report()
        self.loop.start()

    def set_command_prompt(self, string):
        self.footer.set_caption(string)
        self.widget.focus_position = 'footer'

    def update_report(self, report=None):
        self.build_main_widget(report)
        self.loop.widget = self.widget

    def build_main_widget(self, report=None):
        if report:
            self.report = report
        self.build_report()
        self.widget = urwid.Frame(
            self.table.listbox,
            header=self.header,
            footer=self.footer,
        )

    def run(self, report):
        self.build_main_widget(report)
        self.loop = urwid.MainLoop(self.widget, PALETTE, unhandled_input=self.key_pressed)
        self.loop.run()
