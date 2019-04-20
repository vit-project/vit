#!/usr/bin/env python

from future.utils import raise_

import subprocess
import re
import time
import copy
from inspect import isfunction, ismethod
from functools import reduce

import urwid

import formatter
from util import clear_screen, string_to_args, is_mouse_event
from process import Command
from task import TaskListModel, TaskAutoComplete
from keybinding_parser import KeybindingParser
import version

from task_list import TaskTable
import event
from multi_widget import MultiWidget
from command_bar import CommandBar
from registry import ActionRegistry
from denotation import DenotationPopupLauncher

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
    ('message status', 'white', 'dark blue', 'standout'),
    ('message error', 'white', 'dark red', 'standout'),
    ('status', 'dark blue', 'black'),
    ('flash off', 'black', 'black', 'standout'),
    ('flash on', 'white', 'black', 'standout'),
    ('pop_up', 'white', 'black'),
    ('button action', 'white', 'dark red'),
    ('button cancel', 'black', 'light gray'),
]

class Application():
    def __init__(self, config, task_config, reports, report):

        self.config = config
        self.task_config = task_config
        self.reports = reports
        self.report = report
        self.extra_filters = []
        self.search_term_active = ''
        self.action_registry = ActionRegistry()
        self.register_global_actions()
        self.register_task_actions()
        self.actions = self.action_registry.actions
        self.command = Command(self.config)
        self.formatter = formatter.Defaults(self.config, self.task_config)
        self.setup_keybindings()
        self.event = event.Emitter()
        self.event.listen('command-bar:keypress', self.command_bar_keypress)
        self.event.listen('task:denotate', self.denotate_task)
        self.run(self.report)

    def register_global_actions(self):
        register = self.action_registry.register
        register('QUIT', 'Quit the application', self.quit)
        register('QUIT_WITH_CONFIRM', 'Quit the application, after confirmation', self.activate_command_bar_quit_with_confirm)
        register('TASK_ADD', 'Add a task', self.activate_command_bar_add)
        register('REPORT_FILTER', 'Filter current report', self.activate_command_bar_filter)
        register('TASK_UNDO', 'Undo last task change', self.activate_command_bar_undo)
        register('COMMAND_BAR_EX', "Open the command bar in 'ex' mode", self.activate_command_bar_ex)
        register('COMMAND_BAR_EX_TASK_READ_WAIT', "Open the command bar in 'ex' mode with '!rw task ' appended", self.activate_command_bar_ex_read_wait_task)
        register('COMMAND_BAR_SEARCH_FORWARD', 'Open the command bar in search forward mode', self.activate_command_bar_search_forward)
        register('COMMAND_BAR_SEARCH_REVERSE', 'Open the command bar in search reverse mode', self.activate_command_bar_search_reverse)
        register('COMMAND_BAR_SEARCH_NEXT', 'Search next', self.activate_command_bar_search_next)
        register('COMMAND_BAR_SEARCH_PREVIOUS', 'Search previous', self.activate_command_bar_search_previous)
        register('COMMAND_REFRESH_REPORT', 'Refresh the current report', self.update_report)
        register('GLOBAL_ESCAPE', 'Top-level escape function', self.global_escape)
        register('NOOP', 'Used to disable a default keybinding action', self.action_registry.noop)

    def register_task_actions(self):
        register = self.action_registry.register
        register('TASK_ANNOTATE', 'Add an annotation to a task', self.task_action_annotate)
        register('TASK_DELETE', 'Delete task', self.task_action_delete)
        register('TASK_DENOTATE', 'Denotate a task', self.task_action_denotate)
        register('TASK_MODIFY', 'Modify task', self.task_action_modify)
        register('TASK_START_STOP', 'Start/stop task', self.task_action_start_stop)
        register('TASK_DONE', 'Mark task done', self.task_action_done)
        register('TASK_PRIORITY', 'Modify task priority', self.task_action_priority)
        register('TASK_PROJECT', 'Modify task project', self.task_action_project)
        register('TASK_TAGS', 'Modify task tags', self.task_action_tags)
        register('TASK_WAIT', 'Wait a task', self.task_action_wait)
        register('TASK_EDIT', 'Edit a task via the default editor', self.task_action_edit)
        register('TASK_SHOW', 'Show task details', self.task_action_show)

    def setup_keybindings(self):
        self.keybinding_parser = KeybindingParser(self.config, self.actions)
        bindings = self.config.items('keybinding')
        def task_id():
            uuid, _ = self.get_focused_task()
            return uuid
        replacements = {
            'TASKID': task_id,
        }
        self.keybinding_parser.add_keybindings(bindings=bindings, replacements=replacements)
        self.keybindings = self.keybinding_parser.keybindings
        self.keybinding_parser.build_multi_key_cache()
        self.multi_key_cache = self.keybinding_parser.multi_key_cache
        self.cached_keys = ''

    def execute_keybinding(self, keybinding):
        keys = keybinding['keys']
        if isfunction(keys) or ismethod(keys):
            keys()
        else:
            keypresses = self.prepare_keybinding_keypresses(keys)
            self.loop.process_input(keypresses)

    def prepare_keybinding_keypresses(self, keypresses):
        def reducer(accum, key):
            if isfunction(key):
                accum += list(key())
            else:
                accum.append(key)
            return accum
        return reduce(reducer, keypresses, [])

    def denotate_task(self, data):
        task = self.model.task_denotate(data['uuid'], data['annotation'])
        if task:
            self.table.flash_focus()
            self.update_report()
            self.activate_message_bar('Task %s denotated' % self.model.task_id(task['uuid']))
            self.task_list.focus_by_task_uuid(data['uuid'])

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
            elif op == 'delete' and choice is not None:
                task = self.model.task_delete(metadata['uuid'])
                if task:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s deleted' % self.model.task_id(task['uuid']))
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
                metadata = self.ex(data['text'], data['metadata'])
            elif op == 'filter':
                self.extra_filters = args
                self.update_report()
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
                elif op in ('search-forward', 'search-reverse'):
                    self.search_set_term(data['text'])
                    self.search(reverse=(op == 'search-reverse'))
        self.widget.focus_position = 'body'
        if 'uuid' in metadata:
            self.task_list.focus_by_task_uuid(metadata['uuid'])

    def key_pressed(self, key):
        if is_mouse_event(key):
            return None
        keys = self.get_cached_keys(key)
        # NOTE: Colon and equals sign can't be used as config keys, so this
        # is currently obtained from config.
        if key in (self.config.get('command_bar', 'hotkey'),):
            self.set_cached_keys()
            self.activate_command_bar_ex()
        elif keys in self.keybindings:
            self.set_cached_keys()
            self.execute_keybinding(self.keybindings[keys])
        elif keys in self.multi_key_cache:
            self.set_cached_keys(keys)
        else:
            self.set_cached_keys()

    def get_cached_keys(self, key=None):
        return '%s%s' % (self.cached_keys, key) if key else self.cached_keys

    def set_cached_keys(self, keys=''):
        self.cached_keys = keys
        self.update_status_key_cache(self.cached_keys)

    def on_select(self, row, size, key):
        keys = self.get_cached_keys(key)
        self.activate_message_bar()
        # NOTE: Colon and equals sign can't be used as config keys, so this
        # is currently obtained from config.
        if keys in (self.config.get('task', 'show_hotkey'),):
            self.set_cached_keys()
            self.task_action_show()
        elif keys in self.keybindings:
            self.set_cached_keys()
            self.execute_keybinding(self.keybindings[keys])
        else:
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
                metadata.pop('uuid')
            elif command in self.reports:
                self.extra_filters = args
                self.update_report(command)
                metadata.pop('uuid')
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
        return metadata

    def search_set_term(self, text):
        self.search_term_active = text

    def search(self, reverse=False):
        if not self.search_term_active:
            return
        self.search_display_message(reverse)
        current_index = 0 if self.task_list.focus is None else self.task_list.focus_position
        new_focus = self.search_rows(self.search_term_active, current_index, reverse)
        if new_focus is None:
            self.activate_message_bar("Pattern not found: %s" % self.search_term_active, 'error')
        else:
            self.task_list.focus_position = new_focus

    def search_rows(self, term, start_index=0, reverse=False):
        search_regex = re.compile(term, re.MULTILINE)
        rows = self.table.rows
        current_index = start_index
        last_index = len(rows) - 1
        start_matches = self.search_row_has_search_term(rows[start_index], search_regex)
        current_index = self.search_increment_index(current_index, reverse)
        while True:
            if reverse and current_index < 0:
                self.search_loop_warning('TOP', reverse)
                current_index = last_index
            elif not reverse and current_index > last_index:
                self.search_loop_warning('BOTTOM', reverse)
                current_index = 0
            if self.search_row_has_search_term(rows[current_index], search_regex):
                return current_index
            current_index = self.search_increment_index(current_index, reverse)
            if current_index == start_index:
                return start_index if start_matches else None

    def search_increment_index(self, current_index, reverse=False):
        return current_index + (-1 if reverse else 1)

    def search_display_message(self, reverse=False):
        self.activate_message_bar("Search %s for: %s" % ('reverse' if reverse else 'forward', self.search_term_active))

    def search_loop_warning(self, hit, reverse=False):
        self.activate_message_bar('Search hit %s, continuing at %s' % (hit, hit == 'TOP' and 'BOTTOM' or 'TOP'))
        self.loop.draw_screen()
        time.sleep(0.8)
        self.search_display_message(reverse)

    def search_row_has_search_term(self, row, search_regex):
        for column in row.data:
            value = row.data[column]
            if value and search_regex.search(value):
                return True
        return False

    def get_focused_task(self):
        if self.widget.focus_position == 'body':
            try:
                uuid = self.task_list.focus.uuid
                task = self.model.get_task(uuid)
                return uuid, task
            except:
                pass
        return False, False

    def quit(self):
        raise urwid.ExitMainLoop()

    def build_task_table(self):
        self.table = TaskTable(self.config, self.task_config, self.formatter, on_select=self.on_select, event=self.event)

    def update_task_table(self):
        self.table.update_data(self.reports[self.report], self.model.tasks)

    def init_task_list(self):
        self.model = TaskListModel(self.task_config, self.reports)

    def build_frame(self):
        self.status_report = urwid.AttrMap(urwid.Text('Welcome to VIT'), 'status')
        self.status_context = urwid.AttrMap(urwid.Text(''), 'status')
        self.status_performance = urwid.AttrMap(urwid.Text('', align='center'), 'status')
        self.status_version = urwid.AttrMap(urwid.Text('vit (%s)' % version.VIT, align='center'), 'status')
        self.status_tasks_shown = urwid.AttrMap(urwid.Text('', align='right'), 'status')
        self.status_tasks_completed = urwid.AttrMap(urwid.Text('', align='right'), 'status')
        self.top_column_left = urwid.Pile([
            self.status_report,
            self.status_context,
        ])
        self.top_column_center = urwid.Pile([
            self.status_version,
            self.status_performance,
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

    def activate_command_bar_add(self):
        self.activate_command_bar('add', 'Add: ')

    def activate_command_bar_filter(self):
        self.activate_command_bar('filter', 'Filter: ')

    def activate_command_bar_undo(self):
        self.execute_command(['task', 'undo'])

    def activate_command_bar_quit_with_confirm(self):
        self.activate_command_bar('quit', 'Quit?', {'choices': {'y': True}})

    def activate_command_bar_ex(self):
        metadata = {}
        uuid, _ = self.get_focused_task()
        if uuid:
            metadata['uuid'] = uuid
        self.activate_command_bar('ex', ':', metadata)

    def activate_command_bar_ex_read_wait_task(self):
        self.activate_command_bar('ex', ':', {}, edit_text='!rw task ')

    def activate_command_bar_search_forward(self):
        self.activate_command_bar('search-forward', '/')

    def activate_command_bar_search_reverse(self):
        self.activate_command_bar('search-reverse', '?')

    def activate_command_bar_search_next(self):
        self.search()

    def activate_command_bar_search_previous(self):
        self.search(reverse=True)

    def global_escape(self):
        self.denotation_pop_up.close_pop_up()

    def task_action_annotate(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('annotate', 'Annotate: ', {'uuid': uuid})
            self.task_list.focus_by_task_uuid(uuid)

    def task_action_delete(self):
        uuid, task = self.get_focused_task()
        if task:
            task_id = task['id']
            self.activate_command_bar('delete', 'Delete task %s? (y/n): ' % task_id, {'uuid': uuid, 'id': task_id, 'choices': {'y': True}})

    def task_action_denotate(self):
        uuid, task = self.get_focused_task()
        if task and task['annotations']:
                self.denotation_pop_up.open(task)

    def task_action_modify(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('modify', 'Modify: ', {'uuid': uuid})
            self.task_list.focus_by_task_uuid(uuid)

    def task_action_start_stop(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            task = self.model.get_task(uuid)
            if task:
                task_id = task['id']
                self.activate_command_bar('start-stop', '%s task %s? (y/n): ' % (task.active and 'Stop' or 'Start', task_id), {'uuid': uuid, 'choices': {'y': True}})

    def task_action_done(self):
        uuid, task = self.get_focused_task()
        if task:
            task_id = task['id']
            self.activate_command_bar('done', 'Mark task %s done? (y/n): ' % task_id, {'uuid': uuid, 'id': task_id, 'choices': {'y': True}})

    def task_action_priority(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            choices = {
                'h': 'H',
                'm': 'M',
                'l': 'L',
                'n': '',
            }
            self.activate_command_bar('priority', 'Priority (h/m/l/n): ', {'uuid': uuid, 'choices': choices})

    def task_action_project(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('project', 'Project: ', {'uuid': uuid})

    def task_action_tags(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('tag', 'Tag: ', {'uuid': uuid})

    def task_action_wait(self):
        # TODO: Detect if task is already waiting, if so do confirm to un-wait.
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('wait', 'Wait: ', {'uuid': uuid})

    def task_action_edit(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.execute_command(['task', uuid, 'edit'])
            self.task_list.focus_by_task_uuid(uuid)

    def task_action_show(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.execute_command(['task', uuid, 'info'], update_report=False)
            self.task_list.focus_by_task_uuid(uuid)

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

    def update_status_report(self):
        filtered_report = 'task %s %s' % (self.report, ' '.join(self.extra_filters))
        self.status_report.original_widget.set_text(filtered_report)

    def update_status_performance(self, seconds):
        text = 'Exec. time: %dms' % (seconds * 1000)
        self.status_performance.original_widget.set_text(text)

    # TODO: This is riding on top of status_performance currently, should
    # probably be abstracted
    def update_status_key_cache(self, keys):
        text = 'Key cache: %s' % keys if keys else ''
        self.status_performance.original_widget.set_text(text)

    def update_status_context(self):
        returncode, stdout, stderr = self.command.run(['task', 'context', 'show'], capture_output=True)
        if returncode == 0:
            text = ' '.join(stdout.split()[:2])
            self.status_context.original_widget.set_text(text)
        else:
            raise_(RuntimeError, "Error retrieving current context: %s" % stderr)

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
            raise_(RuntimeError, "Error retrieving completed tasks: %s" % stderr)

    def update_report(self, report=None):
        start = time.time()
        if report:
            self.report = report
        self.model.update_report(self.report, self.extra_filters)
        self.update_task_table()
        self.update_status_report()
        self.update_status_context()
        self.update_status_tasks_shown()
        self.update_status_tasks_completed()
        self.header.contents[1] = (self.table.header, self.header.options())
        self.denotation_pop_up = DenotationPopupLauncher(self.table.listbox, self.formatter, event=self.event)
        self.task_list = self.table.listbox
        self.widget.body = self.denotation_pop_up
        self.autocomplete.refresh()
        end = time.time()
        self.update_status_performance(end - start)

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
        self.loop = urwid.MainLoop(self.widget, PALETTE, unhandled_input=self.key_pressed, pop_ups=True)
        self.table.set_draw_screen_callback(self.loop.draw_screen)
        self.loop.run()
