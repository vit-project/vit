from operator import itemgetter
from collections import OrderedDict
from itertools import repeat
from functools import partial
from time import sleep
import re
from functools import cmp_to_key

import urwid
import util

MAX_COLUMN_WIDTH = 60
MARKER_COLUMN_NAME = 'markers'
BRACKETS_REGEX = re.compile("[<>]")

class TaskTable(object):

    def __init__(self, config, task_config, formatter, on_select=None, event=None, action_registry=None, request_reply=None, markers=None):
        self.config = config
        self.task_config = task_config
        self.formatter = formatter
        self.on_select = on_select
        self.event = event
        self.action_registry = action_registry
        self.request_reply = request_reply
        self.markers = markers
        self.register_task_list_actions()
        self.row_striping = self.config.row_striping_enabled()

    def set_draw_screen_callback(self, callback):
        self.draw_screen = callback

    def init_event_listeners(self):
        def signal_handler():
            self.update_focus()
        self.modified_signal = urwid.connect_signal(self.list_walker, 'modified', signal_handler)
        def task_list_keypress(data):
            self.update_header(data['size'])
        self.event.listen('task-list:keypress', task_list_keypress)

    def get_blocking_task_uuids(self):
        return self.request_reply.request('application:blocking_task_uuids')

    def register_task_list_actions(self):
        self.action_registrar = self.action_registry.get_registrar()
        self.action_registrar.register('TASK_LIST_UP', 'Move task list focus up one entry', self.keypress_up)
        self.action_registrar.register('TASK_LIST_DOWN', 'Move task list focus down one entry', self.keypress_down)
        self.action_registrar.register('TASK_LIST_PAGE_UP', 'Move task list focus up one page', self.keypress_page_up)
        self.action_registrar.register('TASK_LIST_PAGE_DOWN', 'Move task list focus down one page', self.keypress_page_down)
        self.action_registrar.register('TASK_LIST_HOME', 'Move task list focus to top of the list', self.keypress_home)
        self.action_registrar.register('TASK_LIST_END', 'Move task list focus to bottom of the list', self.keypress_end)
        self.action_registrar.register('TASK_LIST_SCREEN_TOP', 'Move task list focus to top of the screen', self.keypress_screen_top)
        self.action_registrar.register('TASK_LIST_SCREEN_MIDDLE', 'Move task list focus to middle of the screen', self.keypress_screen_middle)
        self.action_registrar.register('TASK_LIST_SCREEN_BOTTOM', 'Move task list focus to bottom of the screen', self.keypress_screen_bottom)
        self.action_registrar.register('TASK_LIST_FOCUS_VALIGN_CENTER', 'Move focused task to center of the screen', self.keypress_focus_valign_center)
        self.registered_actions = self.action_registrar.actions()

    # NOTE: The non-standard key presses work around infinite recursion while
    #       allowing the up, down, page up, and page down keys to be controlled
    #       from the keybinding file.
    def keypress_up(self, size):
        self.listbox.keypress(size, '<Up>')

    def keypress_down(self, size):
        self.listbox.keypress(size, '<Down>')

    def keypress_page_up(self, size):
        self.listbox.keypress(size, '<Page Up>')

    def keypress_page_down(self, size):
        self.listbox.keypress(size, '<Page Down>')

    def keypress_home(self, size):
        self.listbox.set_focus(0)

    def keypress_end(self, size):
        self.listbox.set_focus(len(self.listbox.body) - 1)
        self.listbox.set_focus_valign('bottom')

    def keypress_screen_top(self, size):
        top, _, _ = self.listbox.get_top_middle_bottom_rows(size)
        self.listbox.focus_by_task_uuid(top.uuid)

    def keypress_screen_middle(self, size):
        _, middle, _ = self.listbox.get_top_middle_bottom_rows(size)
        self.listbox.focus_by_task_uuid(middle.uuid)

    def keypress_screen_bottom(self, size):
        _, _, bottom = self.listbox.get_top_middle_bottom_rows(size)
        self.listbox.focus_by_task_uuid(bottom.uuid)

    def keypress_focus_valign_center(self, size):
        self.listbox.set_focus(self.listbox.focus_position)
        self.listbox.set_focus_valign('middle')

    def update_data(self, report, tasks):
        self.report = report
        self.tasks = tasks
        self.columns = OrderedDict()
        self.rows = []
        self.sort()
        if self.markers.enabled:
            self.add_markers_column()
        self.set_column_metadata()
        if self.markers.enabled:
            self.set_marker_columns()
            self.inject_marker_formatter()
        self.indent_subprojects = self.subproject_indentable()
        self.project_cache = {}
        self.build_rows()
        # TODO: Make this optional based on Taskwarrior config setting.
        self.clean_empty_columns()
        self.reconcile_column_width_for_label()
        self.build_table()
        self.update_focus()

    def update_header(self, size):
        self.update_project_column_header(size)

    def get_project_from_row(self, row):
        return row.task['project'] if isinstance(row, SelectableRow) else row.project

    def update_project_column_header(self, size):
        if self.indent_subprojects:
            top, _, _ = self.listbox.get_top_middle_bottom_rows(size)
            project = self.get_project_from_row(top)
            if project:
                _, parents = util.project_get_subproject_and_parents(project)
                self.set_project_column_header(parents)
            else:
                self.set_project_column_header()

    def set_project_column_header(self, parents=None):
        column_index = self.task_config.get_column_index(self.report['name'], 'project')
        if self.has_marker_column():
            column_index += 1
        (widget, _) = self.header.original_widget.contents[column_index]
        label = self.project_label_for_parents(parents)
        widget.set_text(label)

    def project_label_for_parents(self, parents):
        return '.'.join(parents) if parents else self.task_config.get_column_label(self.report['name'], 'project')

    def update_focus(self):
        if len(self.contents) > 0:
            if self.listbox.previous_focus_position != self.listbox.focus_position:
                if self.listbox.previous_focus_position is not None and self.listbox.previous_focus_position < len(self.contents):
                    self.contents[self.listbox.previous_focus_position].reset_attr_map()
                if self.listbox.focus_position is not None:
                    self.update_focus_attr('reveal focus')
            self.listbox.previous_focus_position = self.listbox.focus_position
        else:
            self.listbox.previous_focus_position = None

    def update_focus_attr(self, attr, position=None):
        if position is None:
            position = self.listbox.focus_position
        self.contents[position].row.set_attr_map({None: attr})

    def flash_focus(self, repeat_times=2, pause_seconds=0.1):
        if len(self.contents) > 0:
            position = self.listbox.focus_position if self.listbox.focus_position is not None else self.listbox.previous_focus_position if self.listbox.previous_focus_position is not None else None
            if position is not None:
                self.update_focus_attr('flash on', position)
                self.draw_screen()
                for i in repeat(None, repeat_times):
                    sleep(pause_seconds)
                    self.update_focus_attr('flash off', position)
                    self.draw_screen()
                    sleep(pause_seconds)
                    self.update_focus_attr('flash on', position)
                    self.draw_screen()
                sleep(pause_seconds)
                self.update_focus_attr('reveal focus', position)
                self.draw_screen()

    def sort(self):
        for column, order, collate in reversed(self.report['sort']):
            def comparator(first, second):
                if first[column] is not None and second[column] is not None:
                    return -1 if first[column] < second[column] else 1 if first[column] > second[column] else 0
                elif first[column] is None and second[column] is None:
                    return 0
                elif first[column] is not None and second[column] is None:
                    return 1
                elif first[column] is None and second[column] is not None:
                    return -1
            if order and order == 'descending':
                self.tasks = sorted(self.tasks, key=cmp_to_key(comparator), reverse=True)
            else:
                self.tasks = sorted(self.tasks, key=cmp_to_key(comparator))

    def column_formatter_kwargs(self):
        kwargs = {}
        if 'dateformat' in self.report:
            kwargs['custom_formatter'] = self.report['dateformat']
        return kwargs

    def add_markers_column(self):
        name, _ = self.formatter.get(MARKER_COLUMN_NAME)
        self.columns[name] = {
            'label': self.markers.header_label,
            'width': 0,
            'align': 'right',
        }

    def set_marker_columns(self):
        self.report_marker_columns = [c for c in self.markers.columns if c not in self.columns]

    def inject_marker_formatter(self):
        name, formatter_class = self.formatter.get(MARKER_COLUMN_NAME)
        self.columns[name]['formatter'] = formatter_class(self.report, self.formatter, self.report_marker_columns, self.get_blocking_task_uuids())

    def set_column_metadata(self):
        kwargs = self.column_formatter_kwargs()
        for idx, column_formatter in enumerate(self.report['columns']):
            name, formatter_class = self.formatter.get(column_formatter)
            self.columns[name] = {
                'label': self.report['labels'][idx],
                'formatter': formatter_class(name, self.report, self.formatter, **kwargs),
                'width': 0,
                'align': 'left',
            }

    def is_marker_column(self, column):
        return column == MARKER_COLUMN_NAME

    def has_marker_column(self):
        return MARKER_COLUMN_NAME in self.columns

    def build_rows(self):
        self.task_row_striping_reset()
        for task in self.tasks:
            row_data = {}
            self.inject_project_placeholders(task)
            alt_row = self.task_row_striping()
            for column, metadata in list(self.columns.items()):
                formatted_value = metadata['formatter'].format(task[column], task)
                width, text_markup = self.build_row_column(formatted_value)
                self.update_column_width(column, metadata['width'], width)
                row_data[column] = text_markup
            self.rows.append(TaskRow(task, row_data, alt_row))

    def update_column_width(self, column, current_width, new_width):
        if new_width > current_width and current_width < MAX_COLUMN_WIDTH:
            self.columns[column]['width'] = new_width if new_width < MAX_COLUMN_WIDTH else MAX_COLUMN_WIDTH

    def build_row_column(self, formatted_value):
        if isinstance(formatted_value, tuple):
            return formatted_value
        else:
            width = len(formatted_value) if formatted_value else 0
            return width, formatted_value

    def subproject_indentable(self):
        return self.config.subproject_indentable and self.report['subproject_indentable']

    def inject_project_placeholders(self, task):
        project = task['project']
        if self.indent_subprojects and project:
            parents = self.project_may_need_placeholders(project)
            if parents:
                to_inject = self.build_project_placeholders_to_inject(parents, [])
                for project_parts in to_inject:
                    self.inject_project_placeholder(project_parts)

    def build_project_placeholders_to_inject(self, parents, to_inject):
        project = '.'.join(parents)
        if project in self.project_cache:
            return to_inject
        else:
            self.project_cache[project] = True
            to_inject.append(parents.copy())
            parents.pop()
            if len(parents) > 0:
                return self.build_project_placeholders_to_inject(parents, to_inject)
            else:
                to_inject.reverse()
                return to_inject

    def project_may_need_placeholders(self, project):
        if project not in self.project_cache:
            self.project_cache[project] = True
            _, parents = util.project_get_subproject_and_parents(project)
            return parents

    def inject_project_placeholder(self, project_parts):
        project = '.'.join(project_parts)
        (width, spaces, indicator, subproject) = self.formatter.format_subproject_indented(project_parts)
        # TODO: This is pretty ugly...
        alt_row = self.task_row_striping()
        self.rows.append(ProjectRow(project, [spaces, indicator, (self.columns['project']['formatter'].colorize(project), subproject)], alt_row))

    def clean_empty_columns(self):
        self.columns = {c:m for c,m in list(self.columns.items()) if m['width'] > 0}

    def reconcile_column_width_for_label(self):
        for column, metadata in list(self.columns.items()):
            label_len = len(metadata['label'])
            if metadata['width'] < label_len:
                self.columns[column]['width'] = label_len

    def get_alt_row_background_modifier(self):
        return '.striped-table-row'

    def task_row_striping_reset(self):
        self.task_alt_row = False

    def task_row_striping(self):
        if self.row_striping:
            self.task_alt_row = not self.task_alt_row
            modifier = self.task_alt_row and self.get_alt_row_background_modifier() or ''
            self.formatter.task_colorizer.set_background_modifier(modifier)
        return self.task_alt_row

    def build_table(self):
        self.contents = [SelectableRow(self.columns, obj, on_select=self.on_select) if isinstance(obj, TaskRow) else ProjectPlaceholderRow(self.columns, obj) for obj in self.rows]
        self.list_walker = urwid.SimpleFocusListWalker(self.contents)
        self.listbox = TaskListBox(self.list_walker, event=self.event, request_reply=self.request_reply, registered_actions=self.registered_actions)
        self.init_event_listeners()
        list_header = urwid.Columns([(metadata['width'] + 2, urwid.Text(metadata['label'], align='left')) for column, metadata in list(self.columns.items())])
        self.header = urwid.AttrMap(list_header, 'list-header')

class TaskRow():
    def __init__(self, task, data, alt_row):
        self.task = task
        self.data = data
        self.alt_row = alt_row
        self.uuid = self.task['uuid']
        self.id = self.task['id']

class ProjectRow():
    def __init__(self, project, placeholder, alt_row):
        self.project = project
        self.placeholder = placeholder
        self.alt_row = alt_row

class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, columns, row, *, on_select=None, space_between=2):
        self.task = row.task
        self.uuid = row.uuid
        self.id = row.id
        self.alt_row = row.alt_row

        self._columns = urwid.Columns([(metadata['width'], urwid.Text(row.data[column], align=metadata['align'])) for column, metadata in list(columns.items())],
                                       dividechars=space_between)
        self.set_display_attr()
        self.row = urwid.AttrMap(self._columns, self.display_attr)

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

        # A hook which defines the behavior that is executed when a specified key is pressed.
        self.on_select = on_select

    def set_display_attr(self):
        self.display_attr = self.alt_row and 'striped-table-row' or ''

    def reset_attr_map(self):
        self.row.set_attr_map({None: self.display_attr})

    def __repr__(self):
        return "{}(id={}, uuid={})".format(self.__class__.__name__,
                                          self.id, self.uuid)

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

class ProjectPlaceholderRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' for a project placeholder row.
    """

    def __init__(self, columns, row, space_between=2):
        self.uuid = None
        self.id = None
        self.alt_row = row.alt_row
        self.project = row.project
        self.placeholder = row.placeholder
        self._columns = urwid.Columns([(metadata['width'], urwid.Text(row.placeholder if column == 'project' else '', align=metadata['align'])) for column, metadata in list(columns.items())], dividechars=space_between)

        self.set_display_attr()
        self.row = urwid.AttrMap(self._columns, self.display_attr)

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

    def set_display_attr(self):
        self.display_attr = self.alt_row and 'striped-table-row' or ''

    def reset_attr_map(self):
        self.row.set_attr_map({None: self.display_attr})
        pass

    def __repr__(self):
        return "{}(placeholder={})".format(self.__class__.__name__, self.placeholder)

class TaskListBox(urwid.ListBox):
    """Maps task list shortcuts to default ListBox class.
    """

    def __init__(self, body, event=None, request_reply=None, registered_actions=None):
        self.previous_focus_position = None
        self.event = event
        self.request_reply = request_reply
        self.registered_actions = registered_actions
        self.keybindings = self.request_reply.request('application:keybindings')
        self.key_cache = self.request_reply.request('application:key_cache')
        return super().__init__(body)

    def get_top_middle_bottom_rows(self, size):
        #try:
            ((_, focused, _, _, _), (_, top_list), (_, bottom_list)) = self.calculate_visible(size)
            top = top_list[len(top_list) - 1][0] if len(top_list) > 0 else None
            bottom = bottom_list[len(bottom_list) - 1][0] if len(bottom_list) > 0 else None
            top_list_reversed = []
            # Neither top_list.reverse() nor reversed(top_list) works here, WTF?
            while True:
                if len(top_list) > 0:
                    row = top_list.pop()
                    top_list_reversed.append(row)
                else:
                    break
            assembled_list = top_list_reversed + [(focused, )] + (bottom_list if bottom else [])
            middle = (assembled_list[:len(assembled_list)//2]).pop()[0]
            return (top or focused), middle, (bottom or focused)
        #except:
        #    # TODO: Log this?
        #    return None, None, None

    def handle_keypress(self, keys):
        # TODO: Some of this can probably be abstracted to a keybinding/action
        # manager.
        return keys in self.keybindings and 'action_name' in self.keybindings[keys] and self.keybindings[keys]['action_name'] in self.registered_actions

    def keypress(self, size, key):
        keys = self.key_cache.get(key)
        if self.handle_keypress(keys):
            data = {
                'keybinding': self.keybindings[keys],
                'size': size,
            }
            self.event.emit('task-list:keypress', data)
            return None
        else:
            # NOTE: These are special key presses passed to allow navigation
            #       keys to be managed via keybinding configuration. They are
            #       converted back to standard key presses here.
            if key in ['<Up>', '<Down>', '<Page Up>', '<Page Down>']:
                key = re.sub(BRACKETS_REGEX, '', key).lower()
            return super().keypress(size, key)

    def focus_by_task_id(self, task_id):
        for idx, row in enumerate(self.body):
            if row.id == task_id:
                self.focus_position = idx
                return

    def focus_by_task_uuid(self, uuid):
        for idx, row in enumerate(self.body):
            if row.uuid == uuid:
                self.focus_position = idx
                return

