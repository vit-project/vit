#!/usr/bin/env python

import subprocess

import urwid

from util import clear_screen
from task import TaskCommand, TaskListModel
from report import TaskTable, SelectableRow, TaskListBox

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

def init_app(task_config, reports, report):

    command = TaskCommand()

    def key_pressed(key):
        if key in ('q', 'Q', 'esc'):
            raise urwid.ExitMainLoop()

    def on_select(row, size, key):
        if key == 'e':
            loop.stop()
            clear_screen()
            subprocess.run(["task", row.uuid, "edit"])
            clear_screen()
            loop.start()
            key = None
        elif key == 'enter':
            loop.stop()
            command.result(["task", row.uuid, "info"])
            loop.start()
            key = None
        return key

    model = TaskListModel(task_config, reports, report)
    table = TaskTable(task_config, reports[report], model.tasks, on_select=on_select)

    header = urwid.Pile([
        urwid.Text('Welcome to PYT'),
        table.header,
    ])
    footer = urwid.Text('Status: ready')

    widget = urwid.Frame(
        table.listbox,
        header=header,
        footer=footer,
    )
    loop = urwid.MainLoop(widget, PALETTE, unhandled_input=key_pressed)
    loop.run()
