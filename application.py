#!/usr/bin/env python

import subprocess

import urwid

from util import clear_screen
from task import TaskCommand, TaskModel
from report import TaskTable

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

class TaskListBox(urwid.ListBox):
    """Maps task list shortcuts to default ListBox class.
    """
    def keypress(self, size, key):
        """Overrides ListBox.keypress method.
        """
        if key in ['j', ' ']:
            self.keypress(size, 'down')
            return True
        if key in ['ctrl f']:
            self.keypress(size, 'page down')
            return True
        if key in ['k']:
            self.keypress(size, 'up')
            return True
        if key in ['ctrl b']:
            self.keypress(size, 'page up')
            return True
        # TODO: Can make 'g' 'gg'?
        if key in ['g', '0']:
            self.set_focus(0)
            return True
        if key in ['G']:
            self.set_focus(len(self.body) - 1)
            self.set_focus_valign('bottom')
            return True
        # TODO: This is wrong, should go to middle line on screen.
        if key in ['M']:
            self.set_focus(self.focus_position)
            self.set_focus_valign('middle')
            return True
        return super().keypress(size, key)


class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, columns, row, *, align="left", on_select=None, space_between=2):
        # A list-like object, where each element represents the value of a column.
        self.task = row.task
        self.uuid = row.uuid

        self._columns = urwid.Columns([(metadata['width'], urwid.Text(row.data[column], align=align)) for column, metadata in list(columns.items())],
                                       dividechars=space_between)
        self._focusable_columns = urwid.AttrMap(self._columns, '', 'reveal focus')

        # Wrap 'urwid.Columns'.
        super().__init__(self._focusable_columns)

        # A hook which defines the behavior that is executed when a specified key is pressed.
        self.on_select = on_select

    def __repr__(self):
        return "{}(contents='{}')".format(self.__class__.__name__,
                                          self.contents)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self.on_select:
            key = self.on_select(self, size, key)
        return key

    def set_contents(self, contents):
        # Update the list record inplace...
        self.contents[:] = contents

        # ... and update the displayed items.
        for t, (w, _) in zip(contents, self._columns.contents):
            w.set_text(t)

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

    model = TaskModel(task_config, reports, report)
    table = TaskTable(task_config, reports[report], model.tasks)

    contents = [SelectableRow(table.columns, task, on_select=on_select) for task in table.rows]

    list_header = urwid.Columns([(metadata['width'] + 2, urwid.Text(metadata['label'], align='left')) for column, metadata in list(table.columns.items())])
    header = urwid.Pile([
        urwid.Text('Welcome to PYT'),
        urwid.AttrMap(list_header, 'list-header'),
    ])
    footer = urwid.Text('Status: ready')

    listbox = TaskListBox(urwid.SimpleFocusListWalker(contents))

    widget = urwid.Frame(
        listbox,
        header=header,
        footer=footer,
    )
    loop = urwid.MainLoop(widget, PALETTE, unhandled_input=key_pressed)
    loop.run()
