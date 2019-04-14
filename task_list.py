from operator import itemgetter
from collections import OrderedDict
from itertools import repeat
from time import sleep
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

import urwid
import formatter

MAX_COLUMN_WIDTH = 60

class TaskTable(object):

    def __init__(self, config, task_config, on_select=None):
        self.config = config
        self.task_config = task_config
        self.on_select = on_select
        self.formatter = formatter.Defaults(self.config, self.task_config)

    def set_draw_screen_callback(self, callback):
        self.draw_screen = callback

    def init_event_listener(self):
        def handler():
            self.update_focus()
        self.modified_signal = urwid.connect_signal(self.list_walker, 'modified', handler)

    def update_data(self, report, tasks):
        self.report = report
        self.tasks = tasks
        self.columns = OrderedDict()
        self.rows = []
        self.sort()
        self.set_column_metadata()
        self.has_project_column = self.columns_have_project()
        self.project_cache = {}
        self.build_rows()
        # TODO: Make this optional based on Taskwarrior config setting.
        self.clean_empty_columns()
        self.reconcile_column_width_for_label()
        self.build_table()
        self.update_focus()

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

    def columns_have_project(self):
        return 'project' in self.columns

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

    def inject_project_placeholders(self, task):
        project = task['project']
        if self.has_project_column and project:
            parts = self.project_may_need_placeholders(project)
            if parts:
                to_inject = self.build_project_placeholders_to_inject(parts)
                for project_parts in to_inject:
                    self.inject_project_placeholder(project_parts)

    def build_project_placeholders_to_inject(self, parts, to_inject=[]):
        project = '.'.join(parts)
        if project in self.project_cache:
            return to_inject
        else:
            self.project_cache[project] = True
            to_inject.append(parts.copy())
            parts.pop()
            if len(parts) > 0:
                return self.build_project_placeholders_to_inject(parts, to_inject=to_inject)
            else:
                to_inject.reverse()
                return to_inject

    def project_may_need_placeholders(self, project):
        if project not in self.project_cache:
            self.project_cache[project] = True
            parts = project.split('.')
            parts.pop()
            return parts

    def inject_project_placeholder(self, project_parts):
        self.rows.append(ProjectRow(self.formatter.format_subproject_indented(project_parts)))

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
        self.listbox = TaskListBox(self.list_walker)
        self.init_event_listener()
        list_header = urwid.Columns([(metadata['width'] + 2, urwid.Text(metadata['label'], align='left')) for column, metadata in list(self.columns.items())])
        self.header = urwid.AttrMap(list_header, 'list-header')

class TaskRow():
    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.uuid = self.task['uuid']
        self.id = self.task['id']

class ProjectRow():
    def __init__(self, placeholder):
        self.placeholder = placeholder

class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, columns, row, *, align="left", on_select=None, space_between=2):
        self.task = row.task
        self.uuid = row.uuid
        self.id = row.id

        self._columns = urwid.Columns([(metadata['width'], urwid.Text(row.data[column], align=align)) for column, metadata in list(columns.items())],
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

class ProjectPlaceholderRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' for a project placeholder row.
    """

    def __init__(self, columns, row, align="left", space_between=2):
        self.uuid = None
        self.id = None
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

    def __init__(self, body):
        self.previous_focus_position = None
        return super().__init__(body)

    def keypress(self, size, key):
        """Overrides ListBox.keypress method.
        """
        if key in ('j', ' '):
            self.keypress(size, 'down')
            return None
        if key in ('ctrl f',):
            self.keypress(size, 'page down')
            return None
        if key in ('k',):
            self.keypress(size, 'up')
            return None
        if key in ('ctrl b',):
            self.keypress(size, 'page up')
            return None
        # TODO: Can make 'g' 'gg'?
        if key in ('g', '0'):
            self.set_focus(0)
            return None
        if key in ('G',):
            self.set_focus(len(self.body) - 1)
            self.set_focus_valign('bottom')
            return None
        if key in ('H', 'M', 'L'):
            try:
                ((_, middle, _, _, _), (_, top_list), (_, bottom_list)) = self.calculate_visible(size)
                top = top_list[len(top_list) - 1][0] if len(top_list) > 0 else None
                bottom = bottom_list[len(bottom_list) - 1][0] if len(bottom_list) > 0 else None
                if key in ('H',):
                    self.focus_by_task_uuid(top.uuid if top else middle.uuid)
                if key in ('M',):
                    # top_list.reverse() is returning None here, WTF?
                    top_list_reversed = []
                    while True:
                        if len(top_list) > 0:
                            row = top_list.pop()
                            top_list_reversed.append(row)
                        else:
                            break
                    assembled_list = top_list_reversed + [(middle, )] + (bottom_list if bottom else [])
                    middle = (assembled_list[:len(assembled_list)//2]).pop()[0]
                    self.focus_by_task_uuid(middle.uuid)
                if key in ('L',):
                    self.focus_by_task_uuid(bottom.uuid if bottom else middle.uuid)
            except:
                # TODO: Log this?
                pass
            return None
        if key in ('ctrl m',):
            self.set_focus(self.focus_position)
            self.set_focus_valign('middle')
            return None
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

