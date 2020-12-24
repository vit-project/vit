#!/usr/bin/env python

from importlib import import_module

import subprocess
# TODO: Use regex module for better PCRE support?
#       https://bitbucket.org/mrabarnett/mrab-regex
import re
import time
import copy
from inspect import isfunction
from functools import reduce

import urwid

from vit import version
from vit.exception import VitException
from vit.formatter_base import FormatterBase
from vit import event
from vit.loader import Loader
from vit.config_parser import ConfigParser, TaskParser
from vit.util import clear_screen, string_to_args, is_mouse_event
from vit.process import Command
from vit.task import TaskListModel
from vit.autocomplete import AutoComplete
from vit.keybinding_parser import KeybindingParser
from vit.help import Help
from vit.key_cache import KeyCache
from vit.actions import Actions
from vit.markers import Markers
from vit.color import TaskColorConfig, TaskColorizer
from vit.task_list import TaskTable
from vit.multi_widget import MultiWidget
from vit.command_bar import CommandBar
from vit.registry import ActionRegistry, RequestReply
from vit.action_manager import ActionManagerRegistry
from vit.denotation import DenotationPopupLauncher

# NOTE: This entire class is a workaround for the fact that urwid catches the
# 'ctrl l' keypress in its unhandled_input code, and prevents that from being
# used for the refresh report functionality. Sadly, that is the default
# keybinding, therefore the only way to make it work is to catch the refresh
# action here in the top frame.
class MainFrame(urwid.Frame):
    def __init__(self, body, header=None, footer=None, focus_part='body', key_cache=None, action_manager=None, refresh=None):
        self.key_cache = key_cache
        self.action_manager = action_manager
        self.refresh = refresh
        self.register_managed_actions()
        super().__init__(body, header, footer, focus_part)

    def register_managed_actions(self):
        self.action_manager_registrar = self.action_manager.get_registrar()
        self.action_manager_registrar.register('REFRESH', self.refresh)

    def keypress(self, size, key):
        keys = self.key_cache.get(key)
        if self.action_manager_registrar.handled_action(keys):
            # NOTE: Calling refresh directly here to avoid the
            # action-manager:action-executed event, which clobbers the load
            # time currently.
            self.refresh()
            return None
        else:
            return super().keypress(size, key)

class Application():
    def __init__(self, option, filters):
        self.extra_filters = filters
        self.loader = Loader()
        self.load_early_config()
        self.set_report()
        self.setup_main_loop()
        self.refresh(False)
        self.loop.run()

    def load_early_config(self):
        self.config = ConfigParser(self.loader)
        self.task_config = TaskParser(self.config)
        self.reports = self.task_config.get_reports()

    def set_report(self):
        if len(self.extra_filters) == 0:
            self.report = self.config.get('report', 'default_report')
        elif self.extra_filters[0] in self.reports:
            self.report = self.extra_filters.pop(0)
        else:
            self.report = self.config.get('report', 'default_filter_only_report')

    def setup_main_loop(self):
        self.loop = urwid.MainLoop(urwid.Text(''), unhandled_input=self.key_pressed, pop_ups=True, handle_mouse=self.config.mouse_enabled)
        try:
            self.loop.screen.set_terminal_properties(colors=256)
        except:
            pass

    def set_active_context(self):
        self.context = self.task_config.get_active_context()

    def load_contexts(self):
        self.contexts = self.task_config.get_contexts()

    def bootstrap(self, load_early_config=True):
        self.loader = Loader()
        if load_early_config:
            self.load_early_config()
        self.load_contexts()
        self.set_active_context()
        self.event = event.Emitter()
        self.setup_config()
        self.search_term_active = ''
        self.search_direction_reverse = False
        self.action_registry = ActionRegistry()
        self.actions = Actions(self.action_registry)
        self.actions.register()
        self.keybinding_parser = KeybindingParser(self.loader, self.config, self.action_registry)
        self.command = Command(self.config)
        self.get_available_task_columns()
        self.setup_keybindings()
        self.action_manager = ActionManagerRegistry(self.action_registry, self.key_cache.keybindings, event=self.event)
        self.register_managed_actions()
        self.markers = Markers(self.config, self.task_config)
        self.theme = self.init_theme()
        self.theme_alt_backgrounds = self.get_theme_alt_backgrounds()
        self.task_color_config = TaskColorConfig(self.config, self.task_config, self.theme, self.theme_alt_backgrounds)
        self.init_task_colors()
        self.task_colorizer = TaskColorizer(self.task_color_config)
        self.formatter = FormatterBase(self.loader, self.config, self.task_config, self.markers, self.task_colorizer)
        self.request_reply = RequestReply()
        self.set_request_callbacks()
        # TODO: TaskTable is dependent on a bunch of setup above, this order
        # feels brittle.
        self.build_task_table()
        self.help = Help(self.keybinding_parser, self.actions.get(), event=self.event, request_reply=self.request_reply, action_manager=self.action_manager)
        self.event.listen('command-bar:keypress', self.command_bar_keypress)
        self.event.listen('task:denotate', self.denotate_task)
        self.event.listen('action-manager:action-executed', self.action_manager_action_executed)
        self.event.listen('help:exit', self.deactivate_help)

    def setup_config(self):
        self.confirm = self.config.confirmation_enabled
        self.wait = self.config.wait_enabled

    def register_managed_actions(self):
        # Global.
        self.action_manager_registrar = self.action_manager.get_registrar()
        self.action_manager_registrar.register('QUIT', self.quit)
        self.action_manager_registrar.register('QUIT_WITH_CONFIRM', self.activate_command_bar_quit_with_confirm)
        self.action_manager_registrar.register('TASK_ADD', self.activate_command_bar_add)
        self.action_manager_registrar.register('REPORT_FILTER', self.activate_command_bar_filter)
        self.action_manager_registrar.register('TASK_UNDO', self.task_undo)
        self.action_manager_registrar.register('TASK_SYNC', self.task_sync)
        self.action_manager_registrar.register('COMMAND_BAR_EX', self.activate_command_bar_ex)
        self.action_manager_registrar.register('COMMAND_BAR_EX_TASK_READ_WAIT', self.activate_command_bar_ex_read_wait_task)
        self.action_manager_registrar.register('COMMAND_BAR_SEARCH_FORWARD', self.activate_command_bar_search_forward)
        self.action_manager_registrar.register('COMMAND_BAR_SEARCH_REVERSE', self.activate_command_bar_search_reverse)
        self.action_manager_registrar.register('COMMAND_BAR_SEARCH_NEXT', self.activate_command_bar_search_next)
        self.action_manager_registrar.register('COMMAND_BAR_SEARCH_PREVIOUS', self.activate_command_bar_search_previous)
        self.action_manager_registrar.register('COMMAND_BAR_TASK_CONTEXT', self.activate_command_bar_task_context)
        self.action_manager_registrar.register('GLOBAL_ESCAPE', self.global_escape)
        self.action_manager_registrar.register(self.action_registry.noop_action_name, self.action_registry.noop)
        # Task.
        self.action_manager_registrar.register('TASK_ANNOTATE', self.task_action_annotate)
        self.action_manager_registrar.register('TASK_DELETE', self.task_action_delete)
        self.action_manager_registrar.register('TASK_DENOTATE', self.task_action_denotate)
        self.action_manager_registrar.register('TASK_MODIFY', self.task_action_modify)
        self.action_manager_registrar.register('TASK_START_STOP', self.task_action_start_stop)
        self.action_manager_registrar.register('TASK_DONE', self.task_action_done)
        self.action_manager_registrar.register('TASK_PRIORITY', self.task_action_priority)
        self.action_manager_registrar.register('TASK_PROJECT', self.task_action_project)
        self.action_manager_registrar.register('TASK_TAGS', self.task_action_tags)
        self.action_manager_registrar.register('TASK_WAIT', self.task_action_wait)
        self.action_manager_registrar.register('TASK_EDIT', self.task_action_edit)
        self.action_manager_registrar.register('TASK_SHOW', self.task_action_show)

    def default_keybinding_replacements(self):
        import json
        from datetime import datetime
        task_replacement_match = re.compile("^TASK_(\w+)$")
        def _task_attribute_match(variable):
            matches = re.match(task_replacement_match, variable)
            if matches:
                attribute = matches.group(1).lower()
                if attribute in self.available_columns:
                    return [attribute]
        def _task_attribute_replace(task, attribute):
            if task and task[attribute]:
                if type(task[attribute]) in ['set', 'tuple', 'dict', 'list']:
                    try:
                        json.dumps(task[attribute])
                    except Exception as e:
                        raise RuntimeError('Error parsing task attribute %s as JSON: %s' % (task[attribute], e))
                elif isinstance(task[attribute], datetime):
                    return task[attribute].strftime(self.formatter.report)
                else:
                    return str(task[attribute])
            return ''
        replacements = [
            {
                'match_callback': _task_attribute_match,
                'replacement_callback': _task_attribute_replace,
            },
        ]
        return replacements

    def add_user_keybinding_replacements(self, replacements):
        klass = self.loader.load_user_class('keybinding', 'keybinding', 'Keybinding')
        if klass:
            keybinding_custom = klass()
            replacements.extend(keybinding_custom.replacements())
        return replacements

    def wrap_replacements_callbacks(self, replacements):
        def build_wrapper(callback):
            def wrapper(*args):
                _, task = self.get_focused_task()
                return callback(task, *args)
            return wrapper
        for i, replacement in enumerate(replacements):
            replacements[i]['replacement_callback'] = build_wrapper(replacement['replacement_callback'])
        return replacements

    def setup_keybindings(self):
        self.keybinding_parser.load_default_keybindings()
        bindings = self.config.items('keybinding')
        replacements = self.wrap_replacements_callbacks(self.add_user_keybinding_replacements(self.default_keybinding_replacements()))
        keybindings = self.keybinding_parser.add_keybindings(bindings=bindings, replacements=replacements)
        self.key_cache = KeyCache(keybindings)
        self.key_cache.build_multi_key_cache()

    def set_request_callbacks(self):
        self.request_reply.set_handler('application:keybindings', 'Get keybindings', lambda: self.keybinding_parser.keybindings)
        self.request_reply.set_handler('application:key_cache', 'Get key cache', lambda: self.key_cache)
        self.request_reply.set_handler('application:blocking_task_uuids', 'Get blocking task uuids', lambda: self.blocking_task_uuids)

    def init_theme(self):
        theme = self.config.get('vit', 'theme')
        user_theme = self.loader.load_user_class('theme', theme, 'theme')
        if user_theme:
            return user_theme
        try:
            return import_module('vit.theme.%s' % theme).theme
        except ImportError:
            raise ImportError("theme '%s' not found" % theme)

    def get_theme_setting(self, setting):
        for s in self.theme:
            if s[0] == setting:
                return s

    def get_theme_alt_backgrounds(self):
        stiped_table_row = self.get_theme_setting('striped-table-row')
        return {
            '.striped-table-row': (stiped_table_row[2], stiped_table_row[5]),
        }

    def init_task_colors(self):
        self.theme += self.task_color_config.display_attrs

    def clear_key_cache(self):
        self.key_cache.set()
        self.update_status_key_cache()

    def action_manager_action_executed(self, data):
        self.clear_key_cache()

    def check_macro(self, keys):
        keybinding = self.keybinding_parser.keybindings[keys] if keys in self.keybinding_parser.keybindings else False
        return keybinding if keybinding and 'keys' in keybinding else False

    def execute_macro(self, keys):
        keybinding = self.check_macro(keys)
        if keybinding:
            keypresses = self.prepare_keybinding_keypresses(keybinding['keys'])
            self.loop.process_input(keypresses)

    def prepare_keybinding_keypresses(self, keypresses):
        def reducer(accum, key):
            if type(key) is tuple:
                accum += list(key[0](*key[1]))
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
            self.task_list.focus_by_task_uuid(data['uuid'], self.previous_focus_position)

    def command_bar_keypress(self, data):
        metadata = data['metadata']
        op = metadata['op']
        if 'choices' in data['metadata']:
            choice = data['choice']
            if op == 'quit' and choice:
                self.quit()
            elif op == 'done' and choice is not None:
                self.task_done(metadata['uuid'])
            elif op == 'delete' and choice is not None:
                self.task_delete(metadata['uuid'])
            elif op == 'start-stop' and choice is not None:
                self.task_start_stop(metadata['uuid'])
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
            elif op == 'project':
                # TODO: Validation if more than one arg passed.
                project = args[0] if len(args) > 0 else ''
                task = self.model.task_project(metadata['uuid'], project)
                if task:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s project updated' % self.model.task_id(task['uuid']))
            elif op == 'wait':
                # TODO: Validation if more than one arg passed.
                wait = args[0] if len(args) > 0 else ''
                # NOTE: Modify is used here to support the special date
                # handling Taskwarrior makes available. It's possible the
                # modified task could be a recurring task, and to make the
                # individual edit actions consistent, recurrence.confirmation
                # is set to 'no', so that only the edited recurring task is
                # modified.
                returncode, stdout, stderr = self.command.run(['task', 'rc.recurrence.confirmation=no', metadata['uuid'], 'modify', 'wait:%s' % wait], capture_output=True)
                if returncode == 0:
                    self.table.flash_focus()
                    self.update_report()
                    self.activate_message_bar('Task %s wait updated' % self.model.task_id(metadata['uuid']))
                else:
                    self.activate_message_bar("Error setting wait: %s" % stderr, 'error')
            elif op == 'context':
                # TODO: Validation if more than one arg passed.
                context = args[0] if len(args) > 0 else 'none'
                if context != 'none':
                    # In case a new context was added between bootstraps.
                    self.load_contexts()
                if self.execute_command(['task', 'context', context], wait=self.wait):
                    self.activate_message_bar('Context switched to: %s' % context)
                else:
                    self.activate_message_bar('Error switching context', 'error')
            elif len(args) > 0:
                if op == 'add':
                    if self.execute_command(['task', 'add'] + args, wait=self.wait):
                        self.activate_message_bar('Task added')
                elif op == 'modify':
                    # TODO: Will this break if user clicks another list item
                    # before hitting enter?
                    if self.execute_command(['task', metadata['uuid'], 'modify'] + args, wait=self.wait):
                        self.activate_message_bar('Task %s modified' % self.model.task_id(metadata['uuid']))
                elif op == 'annotate':
                    task = self.model.task_annotate(metadata['uuid'], data['text'])
                    if task:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Annotated task %s' % self.model.task_id(task['uuid']))
                elif op == 'tag':
                    task = self.model.task_tags(metadata['uuid'], args)
                    if task:
                        self.table.flash_focus()
                        self.update_report()
                        self.activate_message_bar('Task %s tags updated' % self.model.task_id(task['uuid']))
                elif op in ('search-forward', 'search-reverse'):
                    self.search_set_term(data['text'])
                    self.search_set_direction(op)
                    self.search(reverse=(op == 'search-reverse'))
        self.widget.focus_position = 'body'
        if 'uuid' in metadata:
            self.task_list.focus_by_task_uuid(metadata['uuid'], self.previous_focus_position)

    def key_pressed(self, key):
        if is_mouse_event(key):
            return None
        keys = self.key_cache.get(key)
        if self.action_manager_registrar.handled_action(keys):
            self.activate_message_bar()
            self.action_manager_registrar.execute_handler(keys)
        elif self.check_macro(keys):
            self.clear_key_cache()
            self.activate_message_bar()
            self.execute_macro(keys)
        elif keys in self.key_cache.multi_key_cache:
            self.key_cache.set(keys)
            self.update_status_key_cache()
        else:
            self.clear_key_cache()

    def on_select(self, row, size, key):
        keys = self.key_cache.get(key)
        if self.action_manager_registrar.handled_action(keys):
            self.activate_message_bar()
            self.action_manager_registrar.execute_handler(keys)
            return None
        else:
            return key

    def activate_help(self, args):
        [self.original_header_top_contents, self.original_header_bottom_contents] = self.header.contents
        self.original_widget_body = self.widget.body
        self.original_footer = self.footer
        help_widget = self.help.update(args)
        self.header.contents[:] = []
        self.widget.body = help_widget
        self.footer = urwid.Pile([])

    def deactivate_help(self, data):
        self.header.contents[:] = [self.original_header_top_contents, self.original_header_bottom_contents]
        self.widget.body = self.original_widget_body
        self.footer = self.original_footer

    def ex(self, text, metadata):
        args = string_to_args(text)
        if len(args):
            command = args.pop(0)
            if command in ('h', 'help'):
                metadata = {}
                self.activate_help(args)
            elif command in ('q',):
                self.quit()
            elif command in ('!', '!r', '!w', '!rw', '!wr'):
                kwargs = {}
                if command in ('!', '!w'):
                    kwargs['update_report'] = False
                if command in ('!', '!r'):
                    kwargs['confirm'] = None
                    kwargs['wait'] = False
                else:
                    kwargs['wait'] = True
                self.execute_command(args, **kwargs)
            elif command.isdigit():
                self.task_list.focus_by_task_id(int(command))
                if 'uuid' in metadata:
                    metadata.pop('uuid')
            elif command in self.reports:
                self.extra_filters = args
                self.update_report(command)
                if 'uuid' in metadata:
                    metadata.pop('uuid')
            elif command in self.task_config.disallowed_reports:
                self.activate_message_bar("Report '%s' is non-standard, use ':!w task %s'" % (command, command), 'error')
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

    def search_set_direction(self, op):
        self.search_direction_reverse = op == 'search-reverse'

    def search(self, reverse=False):
        if not self.search_term_active:
            return
        self.table.batcher.add(0)
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
            if current_index == start_index:
                return start_index if start_matches else None
            current_index = self.search_increment_index(current_index, reverse)

    def search_increment_index(self, current_index, reverse=False):
        return current_index + (-1 if reverse else 1)

    def search_display_message(self, reverse=False):
        self.activate_message_bar("Search %s for: %s" % ('reverse' if reverse else 'forward', self.search_term_active))

    def search_loop_warning(self, hit, reverse=False):
        self.activate_message_bar('Search hit %s, continuing at %s' % (hit, hit == 'TOP' and 'BOTTOM' or 'TOP'))
        self.loop.draw_screen()
        time.sleep(0.8)
        self.search_display_message(reverse)

    def reconstitute_markup_element_as_string(self, accum, markup):
        if isinstance(markup, tuple):
            _, markup = markup
        return accum + markup

    def reconstitute_markup_as_string(self, markup):
        if isinstance(markup, list):
            return reduce(self.reconstitute_markup_element_as_string, markup, '')
        return self.reconstitute_markup_element_as_string('', markup)

    def search_row_has_search_term(self, row, search_regex):
        # TODO: Cleaner way to detect valid searchable row.
        if hasattr(row, 'data'):
            for column in row.data:
                value = self.reconstitute_markup_as_string(column)
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
        self.table = TaskTable(self.config, self.task_config, self.formatter, self.loop.screen, on_select=self.on_select, event=self.event, action_manager=self.action_manager, request_reply=self.request_reply, markers=self.markers, draw_screen_callback=self.loop.draw_screen)

    def update_task_table(self):
        self.table.update_data(self.reports[self.report], self.model.tasks)

    def init_task_list(self):
        self.model = TaskListModel(self.task_config, self.reports)

    def init_autocomplete(self):
        context_list = list(self.contexts.keys()) + ['none']
        self.autocomplete = AutoComplete(self.config, extra_filters={'report': self.reports.keys(), 'help': self.help.autocomplete_entries(), 'context': context_list})

    def init_command_bar(self):
        abort_backspace = self.config.get('vit', 'abort_backspace')
        self.command_bar = CommandBar(autocomplete=self.autocomplete, abort_backspace=abort_backspace, event=self.event)

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
        self.init_autocomplete()
        self.init_command_bar()
        self.message_bar = urwid.Text('', align='center')
        self.footer.add_widget('command', self.command_bar)
        self.footer.add_widget('message', self.message_bar)

    def command_error(self, returncode, error_message):
        if returncode != 0:
            self.activate_message_bar("Command error: %s" % error_message, 'error')
            return True
        return False

    def execute_command(self, args, **kwargs):
        update_report = True
        wait = True
        if 'update_report' in kwargs:
            update_report = kwargs.pop('update_report')
        if 'wait' in kwargs:
            wait = kwargs.pop('wait')
            if not wait:
                kwargs['confirm'] = None
        self.loop.stop()
        # TODO: This is a shitty hack, if not waiting, then we must
        # override the confirmation setting for recurring tasks.
        if not wait and args[0] == 'task':
            args.insert(1, 'rc.recurrence.confirmation=no')
        def execute():
            returncode, output = self.command.result(args, **kwargs)
            if self.command_error(returncode, output):
                return False
            return True
        success = execute()
        if update_report and success:
            self.update_report()
        self.loop.start()
        return success

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

    def task_undo(self):
        self.execute_command(['task', 'undo'])

    def task_sync(self):
        self.execute_command(['task', 'sync'])

    def activate_command_bar_quit_with_confirm(self):
        if self.confirm:
            self.activate_command_bar('quit', 'Quit?', {'choices': {'y': True}})
        else:
            self.quit()

    def activate_command_bar_ex(self):
        metadata = {}
        uuid, _ = self.get_focused_task()
        if uuid:
            metadata['uuid'] = uuid
        self.activate_command_bar('ex', ':', metadata)

    def activate_command_bar_ex_read_wait_task(self):
        self.activate_command_bar('ex', ':', {}, edit_text='!rw task ')

    def activate_command_bar_search_forward(self):
        self.activate_command_bar('search-forward', '/', {'history': 'search'})

    def activate_command_bar_search_reverse(self):
        self.activate_command_bar('search-reverse', '?', {'history': 'search'})

    def activate_command_bar_search_next(self):
        self.search(reverse=self.search_direction_reverse)

    def activate_command_bar_search_previous(self):
        self.search(reverse=not self.search_direction_reverse)

    def activate_command_bar_task_context(self):
        self.activate_command_bar('context', 'Context: ')

    def global_escape(self):
        self.denotation_pop_up.close_pop_up()


    def task_done(self, uuid):
        success, task = self.model.task_done(uuid)
        if task:
            if success:
                self.table.flash_focus()
                self.update_report()
                self.activate_message_bar('Task %s marked done' % self.model.task_id(task['uuid']))
            else:
                self.activate_message_bar('Error: %s' % task, 'error')

    def task_delete(self, uuid):
        success, task = self.model.task_delete(uuid)
        if task:
            if success:
                self.table.flash_focus()
                self.update_report()
                self.activate_message_bar('Task %s deleted' % self.model.task_id(task['uuid']))
            else:
                self.activate_message_bar('Error: %s' % task, 'error')

    def task_start_stop(self, uuid):
        success, task = self.model.task_start_stop(uuid)
        if task:
            if success:
                self.table.flash_focus()
                self.update_report()
                self.activate_message_bar('Task %s %s' % (self.model.task_id(task['uuid']), 'started' if task.active else 'stopped'))
            else:
                self.activate_message_bar('Error: %s' % task, 'error')

    def task_action_annotate(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('annotate', 'Annotate: ', {'uuid': uuid})
            self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_delete(self):
        uuid, task = self.get_focused_task()
        if task:
            if self.confirm:
                self.activate_command_bar('delete', 'Delete task %s? (y/n): ' % self.model.task_id(uuid), {'uuid': uuid, 'choices': {'y': True}})
            else:
                self.task_delete(uuid)
                self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_denotate(self):
        uuid, task = self.get_focused_task()
        if task and task['annotations']:
                self.denotation_pop_up.open(task)

    def task_action_modify(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('modify', 'Modify: ', {'uuid': uuid})
            self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_start_stop(self):
        uuid, task = self.get_focused_task()
        if task:
            if self.confirm:
                self.activate_command_bar('start-stop', '%s task %s? (y/n): ' % (task.active and 'Stop' or 'Start', self.model.task_id(uuid)), {'uuid': uuid, 'choices': {'y': True}})
            else:
                self.task_start_stop(uuid)
                self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_done(self):
        uuid, task = self.get_focused_task()
        if task:
            if self.confirm:
                self.activate_command_bar('done', 'Mark task %s done? (y/n): ' % self.model.task_id(uuid), {'uuid': uuid, 'choices': {'y': True}})
            else:
                self.task_done(uuid)
                self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_priority(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            choices = {}
            for choice in self.task_config.priority_values:
                key = choice.lower() or 'n'
                choices[key] = choice
            self.activate_command_bar('priority', 'Priority (%s): ' % '/'.join(choices), {'uuid': uuid, 'choices': choices})

    def task_action_project(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('project', 'Project: ', {'uuid': uuid})

    def task_action_tags(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('tag', 'Tag: ', {'uuid': uuid})

    def task_action_wait(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.activate_command_bar('wait', 'Wait: ', {'uuid': uuid})

    def task_action_edit(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.execute_command(['task', uuid, 'edit'], wait=self.wait)
            self.task_list.focus_by_task_uuid(uuid, self.previous_focus_position)

    def task_action_show(self):
        uuid, _ = self.get_focused_task()
        if uuid:
            self.execute_command(['task', uuid, 'info'], update_report=False)
            self.task_list.focus_by_task_uuid(uuid)

    def get_available_task_columns(self):
        returncode, stdout, stderr = self.command.run(['task', '_columns'], capture_output=True)
        if returncode == 0:
            self.available_columns = stdout.split()
        else:
            raise RuntimeError("Error retrieving available task columns: %s" % stderr)

    def refresh_blocking_task_uuids(self):
        returncode, stdout, stderr = self.command.run(['task', 'uuids', '+BLOCKING'], capture_output=True)
        if returncode == 0:
            self.blocking_task_uuids = stdout.split()
        else:
            raise RuntimeError("Error retrieving blocking task UUIDs: %s" % stderr)

    def setup_autocomplete(self, op):
        callback = self.command_bar.set_edit_text_callback()
        if op in ('filter', 'add', 'modify'):
            self.autocomplete.setup(callback)
        elif op in ('ex',):
            filters = ('report', 'column', 'project', 'tag', 'help')
            filter_config = copy.deepcopy(self.autocomplete.default_filter_config)
            filter_config['report'] = {
                'include_unprefixed': True,
                'root_only': True,
            }
            filter_config['help'] = {
                'include_unprefixed': True,
                'root_only': True,
            }
            self.autocomplete.setup(callback, filters=filters, filter_config=filter_config)
        elif op in ('project',):
            filters = ('project',)
            filter_config = {
                'project': {
                    'prefixes': [],
                    'include_unprefixed': True,
                },
            }
            self.autocomplete.setup(callback, filters=filters, filter_config=filter_config)
        elif op in ('tag',):
            filters = ('tag',)
            filter_config = {
                'tag': {
                    'prefixes': ['+', '-'],
                    'include_unprefixed': True,
                },
            }
            self.autocomplete.setup(callback, filters=filters, filter_config=filter_config)
        elif op in ('context',):
            filters = ('context',)
            filter_config = {
                'context': {
                    'include_unprefixed': True,
                    'root_only': True,
                },
            }
            self.autocomplete.setup(callback, filters=filters, filter_config=filter_config)

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
    def update_status_key_cache(self):
        keys = self.key_cache.get()
        text = 'Key cache: %s' % keys if keys else ''
        self.status_performance.original_widget.set_text(text)

    def update_status_context(self):
        text = 'Context: %s' % self.context if self.context else 'No context'
        self.status_context.original_widget.set_text(text)

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
            raise RuntimeError("Error retrieving completed tasks: %s" % stderr)

    def refresh(self, load_early_config=True):
        self.bootstrap(load_early_config)
        self.build_main_widget()
        # NOTE: Don't see any other way to clear the old palette.
        self.loop.screen._palette = {}
        self.loop.screen.register_palette(self.theme)
        self.loop.screen.clear()
        self.loop.widget = self.widget

    def update_report(self, report=None):
        start = time.time()
        self.task_list = self.table.listbox
        self.previous_focus_position = self.task_list.focus_position if self.task_list.list_walker else 0
        if report:
            self.report = report
        self.set_active_context()
        self.task_config.get_projects()
        self.refresh_blocking_task_uuids()
        self.formatter.recalculate_due_datetimes()
        context_filters = self.contexts[self.context]['filter'] if self.context else []
        try:
            self.model.update_report(self.report, context_filters=context_filters, extra_filters=self.extra_filters)
        except VitException as err:
            self.activate_message_bar(str(err), 'error')
            return
        self.update_task_table()
        self.update_status_report()
        self.update_status_context()
        self.update_status_tasks_shown()
        self.update_status_tasks_completed()
        self.header.contents[1] = (self.table.header, self.header.options())
        self.denotation_pop_up = DenotationPopupLauncher(self.task_list, self.formatter, self.loop.screen, event=self.event, request_reply=self.request_reply, action_manager=self.action_manager)
        self.widget.body = self.denotation_pop_up
        self.autocomplete.refresh()
        end = time.time()
        self.update_status_performance(end - start)

    def build_main_widget(self, report=None):
        if report:
            self.report = report
        self.init_task_list()
        self.build_frame()
        self.widget = MainFrame(
            urwid.ListBox([]),
            header=self.header,
            footer=self.footer,
            key_cache=self.key_cache,
            action_manager=self.action_manager,
            refresh=self.refresh,
        )
        self.update_report(self.report)
