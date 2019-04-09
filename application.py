#!/usr/bin/env python

from future.utils import raise_

import subprocess
import re
import copy
from inspect import isfunction
from functools import reduce

import urwid

from util import clear_screen, string_to_args, is_mouse_event
from process import Command
from task import TaskListModel, TaskAutoComplete
from keybinding_parser import KeybindingParser
import version

from task_list import TaskTable
import event
from multi_widget import MultiWidget
from command_bar import CommandBar

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
    ('message status', 'white', 'dark blue', 'standout'),
    ('message error', 'white', 'dark red', 'standout'),
    ('status', 'dark blue', 'black'),
    ('flash off', 'black', 'black', 'standout'),
    ('flash on', 'white', 'black', 'standout'),
]

class Application():
    def __init__(self, config, task_config, reports, report):

        self.config = config
        self.task_config = task_config
        self.reports = reports
        self.report = report
        self.command = Command(self.config)
        self.setup_keybindings()
        self.event = event.Emitter()
        self.event.listen('command-bar:keypress', self.command_bar_keypress)
        self.run(self.report)

    def setup_keybindings(self):
        self.keybinding_parser = KeybindingParser()
        bindings = self.config.items('keybinding')
        replacements = {
            'TASKID': lambda: str(self.get_focused_task())
        }
        self.keybinding_parser.add_keybindings(bindings=bindings, replacements=replacements)
        self.keybindings = self.keybinding_parser.keybindings

    def prepare_keybinding_keypresses(self, keypresses):
        def reducer(accum, key):
            if isfunction(key):
                accum += list(key())
            else:
                accum.append(key)
            return accum
        return reduce(reducer, keypresses, [])

    def command_bar_keypress(self, data):
        metadata = data['metadata']
        op = metadata['op']
        if 'choices' in data['metadata']:
            choice = data['choice']
            if op == 'quit' and choice:
                self.quit()
            elif op == 'done' and choice is not None:
                task = self.model.task_done(metadata['uuid'])
                if task:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s marked done' % self.model.task_id(task['uuid']))
            elif op == 'start-stop' and choice is not None:
                task = self.model.task_start_stop(metadata['uuid'])
                if task:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s %s' % (self.model.task_id(task['uuid']), 'started' if task['start'] else 'stopped'))
            elif op == 'priority' and choice is not None:
                task = self.model.task_priority(metadata['uuid'], choice)
                if task:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s priority set to: %s' % (self.model.task_id(task['uuid']), task['priority'] or 'None'))
        elif data['key'] in ('enter',):
            args = string_to_args(data['text'])
            if op == 'ex':
                self.ex(data['text'], data['metadata'])
            elif op == 'filter':
                self.update_report(extra_filters=args)
            elif len(args) > 0:
                if op == 'add':
                    self.execute_command(['task', 'add'] + args)
                    self.activate_message_bar('Task added')
                elif op == 'modify':
                    # TODO: Will this break if user clicks another list item
                    # before hitting enter?
                    self.execute_command(['task', metadata['uuid'], 'modify'] + args)
                elif op == 'annotate':
                    task = self.model.task_annotate(metadata['uuid'], data['text'])
                    if task:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Annotated task %s' % self.model.task_id(task['uuid']))
                elif op == 'project':
                    # TODO: Validation if more than one arg passed.
                    task = self.model.task_project(metadata['uuid'], args[0])
                    if task:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Task %s project updated' % self.model.task_id(task['uuid']))
                elif op == 'tag':
                    task = self.model.task_tags(metadata['uuid'], args)
                    if task:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Task %s tags updated' % self.model.task_id(task['uuid']))
                elif op == 'wait':
                    # TODO: Validation if more than one arg passed.
                    returncode, stdout, stderr = self.command.run(['task', metadata['uuid'], 'modify', 'wait:%s' % args[0]], capture_output=True)
                    if returncode == 0:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Task %s wait updated' % self.model.task_id(metadata['uuid']))
                    else:
                        self.activate_message_bar("Error setting wait: %s" % stderr, 'error')
        self.widget.focus_position = 'body'
        if 'uuid' in metadata:
            self.task_list.focus_by_task_uuid(metadata['uuid'])

    def key_pressed(self, key):
        if is_mouse_event(key):
            return None
        # TODO: Should be 'ZZ'.
        if key in ('Q', 'Z'):
            self.quit()
        elif key in ('a',):
            self.activate_command_bar('add', 'Add: ')
        elif key in ('f',):
            self.activate_command_bar('filter', 'Filter: ')
        elif key in ('u',):
            self.execute_command(['task', 'undo'])
        elif key in ('q',):
            self.activate_command_bar('quit', 'Quit?', {'choices': {'y': True}})
        elif key in ('t', ':'):
            metadata = {}
            uuid = self.get_focused_task()
            if uuid:
                metadata['uuid'] = uuid
            edit_text = '!rw task ' if key in ('t',) else None
            self.activate_command_bar('ex', ':', metadata, edit_text=edit_text)
        elif key in self.keybindings:
            keypresses = self.prepare_keybinding_keypresses(self.keybindings[key])
            self.loop.process_input(keypresses)

    def on_select(self, row, size, key):
        self.activate_message_bar()
        if key in ('A',):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('annotate', 'Annotate: ', {'uuid': uuid})
                self.task_list.focus_by_task_uuid(uuid)
            return None
        elif key in ('m',):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('modify', 'Modify: ', {'uuid': uuid})
                self.task_list.focus_by_task_uuid(uuid)
            return None
        elif key in ('b',):
            uuid = self.get_focused_task()
            if uuid:
                task = self.model.get_task(uuid)
                if task:
                    task_id = task['id']
                    self.activate_command_bar('start-stop', '%s task %s? (y/n): ' % (task.active and 'Stop' or 'Start', task_id), {'uuid': uuid, 'choices': {'y': True}})
            return None
        elif key in ('d',):
            uuid = self.get_focused_task()
            if uuid:
                task = self.model.get_task(uuid)
                if task:
                    task_id = task['id']
                    self.activate_command_bar('done', 'Mark task %s done? (y/n): ' % task_id, {'uuid': uuid, 'id': task_id, 'choices': {'y': True}})
            return None
        elif key in ('P',):
            uuid = self.get_focused_task()
            if uuid:
                choices = {
                    'h': 'H',
                    'm': 'M',
                    'l': 'L',
                    'n': '',
                }
                self.activate_command_bar('priority', 'Priority (h/m/l/n): ', {'uuid': uuid, 'choices': choices})
        elif key in ('p',):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('project', 'Project: ', {'uuid': uuid})
            return None
        elif key in ('T',):
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('tag', 'Tag: ', {'uuid': uuid})
            return None
        elif key in ('w',):
            # TODO: Detect if task is already waiting, if so do confirm to un-wait.
            uuid = self.get_focused_task()
            if uuid:
                self.activate_command_bar('wait', 'Wait: ', {'uuid': uuid})
            return None
        elif key in ('e',):
            uuid = self.get_focused_task()
            if uuid:
                self.execute_command(['task', uuid, 'edit'])
                self.task_list.focus_by_task_uuid(uuid)
            return None
        elif key in ('=', 'enter'):
            uuid = self.get_focused_task()
            if uuid:
                self.execute_command(['task', uuid, 'info'], update_report=False)
                self.task_list.focus_by_task_uuid(uuid)
            return None
        elif key in ('ctrl l',):
            self.update_report()
        return key

    def ex(self, text, metadata):
        args = string_to_args(text)
        if len(args):
            command = args.pop(0)
            if command in ('q',):
                self.quit()
            elif command in ('!', '!r', '!w', '!rw', '!wr'):
                kwargs = {}
                if command in ('!', '!w'):
                    kwargs['update_report'] = False
                if command in ('!', '!r'):
                    kwargs['confirm'] = None
                self.execute_command(args, **kwargs)
            elif command.isdigit():
                self.task_list.focus_by_task_id(int(command))
            elif command in self.reports:
                self.update_report(command, args)
            else:
                # Matches 's/foo/bar/' and s%/foo/bar/, allowing for separators
                # to be any non-word character.
                matches = re.match(r'^%?s(\W)((?:(?!\1).)*)\1((?:(?!\1).)*)\1$', text)
                if matches and 'uuid' in metadata:
                    before, after = matches.group(2, 3)
                    task = self.model.get_task(metadata['uuid'])
                    if task:
                        description = re.sub(r'%s' % before, after, task['description'])
                        task = self.model.task_description(metadata['uuid'], description)
                        if task:
                            self.table.flash_focus()
                            self.update_report()
                            self.activate_message_bar('Task %s description updated' % self.model.task_id(task['uuid']))

    def get_focused_task(self):
        if self.widget.focus_position == 'body':
            try:
                return self.task_list.focus.uuid
            except:
                pass
        return False

    def quit(self):
        raise urwid.ExitMainLoop()

    def build_task_table(self):
        self.table = TaskTable(self.task_config, on_select=self.on_select)

    def update_task_table(self):
        self.table.update_data(self.reports[self.report], self.model.tasks)

    def init_task_list(self):
        self.model = TaskListModel(self.task_config, self.reports)

    def build_frame(self):
        self.status_report = urwid.AttrMap(urwid.Text('Welcome to VIT'), 'status')
        self.status_version = urwid.AttrMap(urwid.Text('vit (%s)' % version.VIT, align='center'), 'status')
        self.status_tasks_shown = urwid.AttrMap(urwid.Text('', align='right'), 'status')
        self.status_tasks_completed = urwid.AttrMap(urwid.Text('', align='right'), 'status')
        self.top_column_left = urwid.Pile([
            self.status_report,
        ])
        self.top_column_center = urwid.Pile([
            self.status_version,
        ])
        self.top_column_right = urwid.Pile([
            self.status_tasks_shown,
            self.status_tasks_completed,
        ])
        self.header = urwid.Pile([
            urwid.Columns([
                self.top_column_left,
                self.top_column_center,
                self.top_column_right,
            ]),
            urwid.Text('Loading...'),
        ])
        self.footer = MultiWidget()
        self.autocomplete = TaskAutoComplete(self.config, extra_filters={'report': self.reports.keys()})
        self.command_bar = CommandBar(autocomplete=self.autocomplete, event=self.event)
        self.message_bar = urwid.Text('', align='center')
        self.footer.add_widget('command', self.command_bar)
        self.footer.add_widget('message', self.message_bar)

    def execute_command(self, args, **kwargs):
        update_report = True
        if 'update_report' in kwargs:
            update_report = kwargs['update_report']
            kwargs.pop('update_report')
        self.loop.stop()
        self.command.result(args, **kwargs)
        if update_report:
            self.update_report()
        self.loop.start()

    def activate_command_bar(self, op, caption, metadata={}, edit_text=None):
        metadata['op'] = op
        self.footer.show_widget('command')
        self.setup_autocomplete(op)
        self.command_bar.activate(caption, metadata, edit_text)
        self.widget.focus_position = 'footer'

    def setup_autocomplete(self, op):
        callback = self.command_bar.set_edit_text_callback()
        if op in ('filter', 'add', 'modify'):
            self.autocomplete.setup(callback)
        elif op in ('ex',):
            filters = ('report', 'column', 'project', 'tag')
            prefixes = copy.deepcopy(self.autocomplete.default_prefixes)
            prefixes['report'] = {
                'include_unprefixed': True,
                'root_only': True,
            }
            self.autocomplete.setup(callback, filters=filters, prefixes=prefixes)
        elif op in ('project',):
            filters = ('project',)
            prefixes = {
                'project': {
                    'prefixes': [],
                    'include_unprefixed': True,
                },
            }
            self.autocomplete.setup(callback, filters=filters, prefixes=prefixes)
        elif op in ('tag',):
            filters = ('tag',)
            prefixes = {
                'tag': {
                    'prefixes': ['+', '-'],
                    'include_unprefixed': True,
                },
            }
            self.autocomplete.setup(callback, filters=filters, prefixes=prefixes)

    def activate_message_bar(self, message='', message_type='status'):
        self.footer.show_widget('message')
        display = 'message %s' % message_type
        self.message_bar.set_text((display, message))

    def update_status_report(self, extra_filters):
        filtered_report = 'task %s %s' % (self.report, ' '.join(extra_filters))
        self.status_report.original_widget.set_text(filtered_report)

    def update_status_tasks_shown(self):
        num_tasks = len(self.model.tasks)
        text = '%s %s shown' % (num_tasks, num_tasks == 1 and 'task' or 'tasks')
        self.status_tasks_shown.original_widget.set_text(text)

    def update_status_tasks_completed(self):
        returncode, stdout, stderr = self.command.run(['task', '+COMPLETED', 'count'], capture_output=True)
        if returncode == 0:
            num_tasks = int(stdout.strip())
            text = '%s %s completed' % (num_tasks, num_tasks == 1 and 'task' or 'tasks')
            self.status_tasks_completed.original_widget.set_text(text)
        else:
            raise "Error retrieving completed tasks: %s" % stderr

    def update_report(self, report=None, extra_filters=[]):
        if report:
            self.report = report
        self.model.update_report(self.report, extra_filters)
        self.update_task_table()
        self.update_status_report(extra_filters)
        self.update_status_tasks_shown()
        self.update_status_tasks_completed()
        self.header.contents[1] = (self.table.header, self.header.options())
        self.task_list = self.widget.body = self.table.listbox
        self.autocomplete.refresh()

    def build_main_widget(self, report=None):
        if report:
            self.report = report
        self.init_task_list()
        self.build_frame()
        self.widget = urwid.Frame(
            urwid.ListBox([]),
            header=self.header,
            footer=self.footer,
        )
        self.build_task_table()
        self.update_report(self.report)

    def run(self, report):
        self.build_main_widget(report)
        self.loop = urwid.MainLoop(self.widget, PALETTE, unhandled_input=self.key_pressed)
        self.table.set_draw_screen_callback(self.loop.draw_screen)
        self.loop.run()
