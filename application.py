#!/usr/bin/env python
#
# Urwid example lazy directory browser / tree view
#    Copyright (C) 2004-2011  Ian Ward
#    Copyright (C) 2010  Kirk McDonald
#    Copyright (C) 2010  Rob Lanphier
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

from __future__ import print_function
import subprocess

import re
import urwid
import curses, sys, os

from functools import partial
from tasklib import TaskWarrior
tw = TaskWarrior()

import pprint

pp = pprint.PrettyPrinter()
pf = pprint.PrettyPrinter(stream=open("/tmp/test",'w'))

PALETTE = [
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

curses.setupterm()
e3_seq = curses.tigetstr('E3') or b''
clear_screen_seq = curses.tigetstr('clear') or b''

def clear_screen():
    os.write(sys.stdout.fileno(), e3_seq + clear_screen_seq)

class TaskRow():
    def __init__(self, task):
        self.task = task
        self.uuid = self.task['uuid']
        self.columns = self.build_columns()

    def build_columns(self):
        width = get_app_width()
        desc_width = get_app_width() - 6
        columns = [
          (6, str(self.task['id'])),
          (60, self.task['description']),
          (10, task_date(self.task, 'scheduled')),
        ]
        return columns


class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, task_row, *, align="left", on_select=None, space_between=2):
        # A list-like object, where each element represents the value of a column.
        self.task = task_row.task
        self.uuid = task_row.uuid

        self._columns = urwid.Columns([(w, urwid.Text(c, align=align)) for (w, c) in task_row.columns],
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

def get_app_width():
  return 80

def task_date(task, attr, fmt='%Y-%m-%d'):
  try:
    return task[attr].strftime(fmt)
  except AttributeError:
    return ''

class TaskModel(object):
    def __init__(self, reports, report=None):

        self.current_task_id = None
        self.reports = reports
        self.report = report
        if report:
            self.update_report(report)

    def add(self, contact):
        pass

    def active_report(self):
        return self.reports[self.report]

    def update_report(self, report):
        self.report = report
        tasks = tw.tasks.filter(*self.active_report()['filter'])
        self.tasks = tasks

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

def user_output(command_args, confirm="Press Enter to continue...", clear=True):
    if clear:
        clear_screen()
    output = subprocess.check_output(command_args)
    print(output.decode("utf-8"))
    if confirm:
        try:
            input(confirm)
        except:
            raw_input(confirm)
    if clear:
        clear_screen()

def init_app(reports, report):

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
            user_output(["task", row.uuid, "info"])
            loop.start()
            key = None
        return key

    model = TaskModel(reports, report)

    #titles=self._model.active_report()['labels'],
    contents = []
    #contents.append(SelectableRow([
    #    (6, "ID"),
    #    (60, "Description"),
    #    (10, "Starts"),
    #]))
    for task in model.tasks:
        contents.append(SelectableRow(TaskRow(task), on_select=on_select))

    header = urwid.Text('Welcome to PYT')
    footer = urwid.Text('Status: ready')

    listbox = urwid.ListBox(urwid.SimpleFocusListWalker(contents))

    widget = urwid.Frame(
        listbox,
        header=header,
        footer=footer,
    )
    loop = urwid.MainLoop(widget, PALETTE, unhandled_input=key_pressed)
    loop.run()
