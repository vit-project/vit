from operator import itemgetter
from collections import OrderedDict
from itertools import repeat
from functools import partial
from time import sleep
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

import urwid
import util

MAX_COLUMN_WIDTH = 60

class TaskTable(object):

    def __init__(self, config, task_config, formatter, on_select=None, event=None, action_registry=None, request_reply=None):
        self.config = config
        self.task_config = task_config
        self.on_select = on_select
        self.event = event
        self.action_registry = action_registry
        self.request_reply = request_reply
        self.formatter = formatter
        self.register_task_list_actions()

    def set_draw_screen_callback(self, callback):
        self.draw_screen = callback

    def init_event_listeners(self):
        def signal_handler():
            self.update_focus()
        self.modified_signal = urwid.connect_signal(self.list_walker, 'modified', signal_handler)
        def task_list_keypress(data):
            self.update_header(data['size'])
        self.event.listen('task-list:keypress', task_list_keypress)

    def register_task_list_actions(self):
        register = self.action_registry.register
        register('TASK_LIST_UP', 'Move task list focus up one entry', self.keypress_up)
        register('TASK_LIST_DOWN', 'Move task list focus down one entry', self.keypress_down)
        register('TASK_LIST_PAGE_UP', 'Move task list focus up one page', self.keypress_page_up)
        register('TASK_LIST_PAGE_DOWN', 'Move task list focus down one page', self.keypress_page_down)
        register('TASK_LIST_HOME', 'Move task list focus to top of the list', self.keypress_home)
        register('TASK_LIST_END', 'Move task list focus to bottom of the list', self.keypress_end)
        register('TASK_LIST_SCREEN_TOP', 'Move task list focus to top of the screen', self.keypress_screen_top)
        register('TASK_LIST_SCREEN_MIDDLE', 'Move task list focus to middle of the screen', self.keypress_screen_middle)
        register('TASK_LIST_SCREEN_BOTTOM', 'Move task list focus to bottom of the screen', self.keypress_screen_bottom)
        register('TASK_LIST_FOCUS_VALIGN_CENTER', 'Move focused task to center of the screen', self.keypress_focus_valign_center)

    def keypress_up(self, size):
        self.listbox.keypress(size, 'up')

    def keypress_down(self, size):
        self.listbox.keypress(size, 'down')

    def keypress_page_up(self, size):
        self.listbox.keypress(size, 'page up')

    def keypress_page_down(self, size):
        self.listbox.keypress(size, 'page down')

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
        self.set_column_metadata()
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
        (widget, _) = self.header.original_widget.contents[column_index]
        label = self.project_label_for_parents(parents)
        widget.set_text(label)

    def project_label_for_parents(self, parents):
        return '.'.join(parents) if parents else self.task_config.get_column_label(self.report['name'], 'project')

    def update_focus(self):
        if len(self.contents) > 0:
            if self.listbox.previous_focus_position != self.listbox.focus_position:
                if self.listbox.previous_focus_position is not None and self.listbox.previous_focus_position < len(self.contents):
                    self.update_focus_attr({}, position=self.listbox.previous_focus_position)
                if self.listbox.focus_position is not None:
                    self.update_focus_attr('reveal focus')
            self.listbox.previous_focus_position = self.listbox.focus_position
        else:
            self.listbox.previous_focus_position = None

    def update_focus_attr(self, attr, position=None):
        attr = attr if isinstance(attr, dict) else {None: attr}
        if position is None:
            position = self.listbox.focus_position
        self.contents[position].row.set_attr_map(attr)

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

    def custom_report_formatter(self):
        return self.report['dateformat'] if 'dateformat' in self.report else None

    def set_column_metadata(self):
        custom_formatter = self.custom_report_formatter()
        for idx, column_formatter in enumerate(self.report['columns']):
            name, formatter_class = self.formatter.get(column_formatter)
            self.columns[name] = {
                'label': self.report['labels'][idx],
                'formatter': formatter_class(self.report, self.formatter, custom_formatter=custom_formatter),
                'width': 0,
            }

    def build_rows(self):
        for task in self.tasks:
            row_data = {}
            self.inject_project_placeholders(task)
            for column, metadata in list(self.columns.items()):
                current = metadata['width']
                formatted_value = metadata['formatter'].format(task[column], task)
                new = len(formatted_value) if formatted_value else 0
                if new > current and current < MAX_COLUMN_WIDTH:
                    self.columns[column]['width'] = new < MAX_COLUMN_WIDTH and new or MAX_COLUMN_WIDTH
                row_data[column] = formatted_value
            self.rows.append(TaskRow(task, row_data))

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
        placeholder = self.formatter.format_subproject_indented(project_parts)
        self.rows.append(ProjectRow(project, placeholder))

    def clean_empty_columns(self):
        self.columns = {c:m for c,m in list(self.columns.items()) if m['width'] > 0}

    def reconcile_column_width_for_label(self):
        for column, metadata in list(self.columns.items()):
            label_len = len(metadata['label'])
            if metadata['width'] < label_len:
                self.columns[column]['width'] = label_len

    def build_table(self):
        self.contents = [SelectableRow(self.columns, obj, on_select=self.on_select) if isinstance(obj, TaskRow) else ProjectPlaceholderRow(self.columns, obj) for obj in self.rows]
        self.list_walker = urwid.SimpleFocusListWalker(self.contents)
        self.listbox = TaskListBox(self.list_walker, event=self.event, request_reply=self.request_reply)
        self.init_event_listeners()
        list_header = urwid.Columns([(metadata['width'] + 2, urwid.Text(metadata['label'], align='left')) for column, metadata in list(self.columns.items())])
        self.header = urwid.AttrMap(list_header, 'list-header')

class TaskRow():
    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.uuid = self.task['uuid']
        self.id = self.task['id']

class ProjectRow():
    def __init__(self, project, placeholder):
        self.project = project
        self.placeholder = placeholder

class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, columns, row, *, align="left", on_select=None, space_between=2):
        self.task = row.task
        self.uuid = row.uuid
        self.id = row.id
        self.align = align

        self._columns = urwid.Columns([(metadata['width'], self.build_column(column, row.data[column])) for column, metadata in list(columns.items())],
                                       dividechars=space_between)
        self.row = urwid.AttrMap(self._columns, '')

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

        # A hook which defines the behavior that is executed when a specified key is pressed.
        self.on_select = on_select

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

    def build_column(self, column, column_data):
        markup = (self.display_attr(column), column_data)
        return urwid.Text(markup, align=self.align)

    def display_attr(self, column):
        if column == 'tags' and self.task['tags']:
            return 'color.tagged'
        return None


class ProjectPlaceholderRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' for a project placeholder row.
    """

    def __init__(self, columns, row, align="left", space_between=2):
        self.uuid = None
        self.id = None
        self.project = row.project
        self.placeholder = row.placeholder
        self._columns = urwid.Columns([(metadata['width'], urwid.Text(row.placeholder if column == 'project' else '', align=align)) for column, metadata in list(columns.items())],
                                       dividechars=space_between)
        self.row = urwid.AttrMap(self._columns, '')

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

    def __repr__(self):
        return "{}(placeholder={})".format(self.__class__.__name__, self.placeholder)

class TaskListBox(urwid.ListBox):
    """Maps task list shortcuts to default ListBox class.
    """

    def __init__(self, body, event=None, request_reply=None):
        self.previous_focus_position = None
        self.event = event
        self.request_reply = request_reply
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

    # TODO: This action_name check is a horrible hack to prevent other
    # keybindings from being corrupted by the partial function logic below.
    def is_task_list_action(self, keybinding):
        return 'action_name' in keybinding and keybinding['action_name'][0:17] == 'ACTION_TASK_LIST_'

    def keybinding_original_action(self, keybinding):
        return keybinding['original_action'] if 'original_action' in keybinding else keybinding['action']

    def keybinding_action_inject_size(self, keybinding, size):
        return partial(keybinding['original_action'], size)

    def keypress(self, size, key):
        keys = self.key_cache.get(key)
        if keys in self.keybindings and self.is_task_list_action(self.keybindings[keys]):
            # NOTE: This swap is necessary to prevent re-injecting multiple
            # size args into the same action callback.
            self.keybindings[keys]['original_action'] = self.keybinding_original_action(self.keybindings[keys])
            self.keybindings[keys]['action'] = self.keybinding_action_inject_size(self.keybindings[keys], size)
            data = {
                'keybinding': self.keybindings[keys],
                'size': size,
            }
            self.event.emit('task-list:keypress', data)
            return None
        else:
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

