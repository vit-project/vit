from operator import itemgetter
from collections import OrderedDict
from itertools import repeat
from functools import partial, reduce
from time import sleep
import re
import math
from functools import cmp_to_key

import urwid

from vit import util
from vit.base_list_box import BaseListBox
from vit.list_batcher import ListBatcher
from vit.formatter.project import Project as ProjectFormatter

REDUCE_COLUMN_WIDTH_LIMIT = 20
COLUMN_PADDING = 2
MARKER_COLUMN_NAME = 'markers'

class TaskTable(object):

    def __init__(self, config, task_config, formatter, screen, on_select=None, event=None, action_manager=None, request_reply=None, markers=None, draw_screen_callback=None):
        self.config = config
        self.task_config = task_config
        self.formatter = formatter
        self.screen = screen
        self.on_select = on_select
        self.event = event
        self.action_manager = action_manager
        self.request_reply = request_reply
        self.markers = markers
        self.draw_screen = draw_screen_callback
        self.list_walker = urwid.SimpleFocusListWalker([])
        self.row_striping = self.config.row_striping_enabled
        self.listbox = TaskListBox(self.list_walker, self.screen, event=self.event, request_reply=self.request_reply, action_manager=self.action_manager)
        self.init_event_listeners()
        self.set_request_callbacks()

    def init_event_listeners(self):
        def signal_handler():
            self.update_focus()
        urwid.connect_signal(self.list_walker, 'modified', signal_handler)
        def task_list_keypress(data):
            self.update_header(data['size'])
        self.event.listen('task-list:keypress', task_list_keypress)
        self.event.listen('task-list:size:change', self.size_changed)
        self.event.listen('task-list:keypress:down', self.task_list_keypress_down)
        self.event.listen('task-list:keypress:page_down', self.task_list_keypress_page_down)
        self.event.listen('task-list:keypress:end', self.task_list_keypress_end)
        self.event.listen('task-list:keypress:focus_valign_center', self.task_list_keypress_focus_valign_center)

    def set_request_callbacks(self):
        self.request_reply.set_handler('task-table:batch:next', 'Render next batch of tasks', lambda: self.get_next_task_batch())

    def get_next_task_batch(self):
        return self.batcher.add()

    def task_list_keypress_down(self, size):
        self.batcher.add(1)

    def task_list_keypress_page_down(self, size):
        _, rows = size
        self.batcher.add(rows)

    def task_list_keypress_end(self, size):
        self.batcher.add(0)

    def task_list_keypress_focus_valign_center(self, size):
        _, rows = size
        half_rows = math.ceil(rows / 2)
        self.batcher.add(half_rows)

    def get_blocking_task_uuids(self):
        return self.request_reply.request('application:blocking_task_uuids')

    def update_data(self, report, tasks):
        self.report = report
        self.tasks = tasks
        self.list_walker.clear()
        self.columns = []
        self.column_names = []
        self.rows = []
        self.sort()
        self.set_column_metadata()
        if self.markers.enabled:
            self.set_marker_columns()
            self.add_markers_column()
        self.indent_subprojects = self.subproject_indentable()
        self.project_cache = {}
        # TODO: This is for the project placeholders, feels sloppy.
        self.project_formatter = ProjectFormatter('project', self.report, self.formatter, self.get_blocking_task_uuids())
        self.build_rows()
        self.clean_columns()
        self.project_column_idx = self.get_project_column_idx()
        self.reconcile_column_width_for_label()
        self.resize_columns()
        self.build_table()
        self.listbox.set_focus_position()
        self.update_focus()

    def update_header(self, size):
        if self.project_column_idx is not None:
            self.update_project_column_header(size)

    def get_project_column_idx(self):
        for idx, column in enumerate(self.columns):
            if column['name'] == 'project':
                return idx
        return None

    def get_project_from_row(self, row):
        return row.task['project'] if isinstance(row, SelectableRow) else row.project

    def update_project_column_header(self, size):
        if self.indent_subprojects:
            top, _, _ = self.listbox.get_top_middle_bottom_rows(size)
            if top:
                project = self.get_project_from_row(top)
                if project:
                    _, parents = util.project_get_subproject_and_parents(project)
                    self.set_project_column_header(parents)
                else:
                    self.set_project_column_header()

    def set_project_column_header(self, parents=None):
        column_index = self.project_column_idx
        (columns_widget, _) = self.header.original_widget.contents[column_index]
        (widget, _) = columns_widget.contents[0]
        label = self.project_label_for_parents(parents)
        widget.original_widget.original_widget.set_text(label)

    def project_label_for_parents(self, parents):
        return '.'.join(parents) if parents else self.task_config.get_column_label(self.report['name'], 'project')

    def update_focus(self):
        if self.listbox.focus:
            if self.listbox.previous_focus_position != self.listbox.focus_position:
                if self.listbox.previous_focus_position is not None and self.listbox.previous_focus_position < len(self.list_walker):
                    self.list_walker[self.listbox.previous_focus_position].reset_attr_map()
                if self.listbox.focus_position is not None:
                    self.update_focus_attr('reveal focus')
                self.listbox.previous_focus_position = self.listbox.focus_position
            else:
                self.update_focus_attr('reveal focus')
        else:
            self.listbox.previous_focus_position = None

    def update_focus_attr(self, attr, position=None):
        if position is None:
            position = self.listbox.focus_position
        self.list_walker[position].row.set_attr_map({None: attr})

    def flash_focus(self, repeat_times=2, pause_seconds=0.1):
        if self.listbox.focus:
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
        if 'sort' in self.report:
            for column, order, collate in reversed(self.report['sort']):
                def comparator(first, second):
                    if first[column] is not None and second[column] is not None:
                        return -1 if first[column] < second[column] else 1 if first[column] > second[column] else 0
                    elif first[column] is None and second[column] is None:
                        return 0
                    elif first[column] is not None and second[column] is None:
                        return -1
                    elif first[column] is None and second[column] is not None:
                        return 1
                if order and order == 'descending':
                    self.tasks = sorted(self.tasks, key=cmp_to_key(comparator), reverse=True)
                else:
                    self.tasks = sorted(self.tasks, key=cmp_to_key(comparator))

    def column_formatter_kwargs(self):
        kwargs = {}
        if 'dateformat' in self.report:
            kwargs['custom_formatter'] = self.report['dateformat']
        return kwargs

    def set_marker_columns(self):
        self.report_marker_columns = [c for c in self.markers.columns if c not in self.column_names]

    def add_markers_column(self):
        name, formatter_class = self.formatter.get(MARKER_COLUMN_NAME)
        self.columns.insert(0, {
            'name': name,
            'label': self.markers.header_label,
            'formatter': formatter_class(self.report, self.formatter, self.report_marker_columns, self.get_blocking_task_uuids()),
            'width': 0,
            'align': 'right',
        })
        self.column_names.insert(0, name)

    def add_column(self, name, label, formatter_class, align='left'):
        self.columns.append({
            'name': name,
            'label': label,
            'formatter': formatter_class,
            'width': 0,
            'align': align,
        })
        self.column_names.append(name)

    def set_column_metadata(self):
        kwargs = self.column_formatter_kwargs()
        for idx, column_formatter in enumerate(self.report['columns']):
            name, formatter_class = self.formatter.get(column_formatter)
            self.add_column(name, self.report['labels'][idx], formatter_class(name, self.report, self.formatter, self.get_blocking_task_uuids(), **kwargs))

    def is_marker_column(self, column):
        return column == MARKER_COLUMN_NAME

    def has_marker_column(self):
        return MARKER_COLUMN_NAME in self.column_names

    def build_rows(self):
        self.task_row_striping_reset()
        for task in self.tasks:
            row_data = []
            self.inject_project_placeholders(task)
            alt_row = self.task_row_striping()
            for idx, column in enumerate(self.columns):
                formatted_value = column['formatter'].format(task[column['name']], task)
                width, text_markup = self.build_row_column(formatted_value)
                self.update_column_width(idx, column['width'], width)
                row_data.append(text_markup)
            self.rows.append(TaskRow(task, row_data, alt_row))

    def update_column_width(self, idx, current_width, new_width):
        if new_width > current_width:
            self.columns[idx]['width'] = new_width

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
        self.rows.append(ProjectRow(project, [spaces, indicator, (self.project_formatter.colorize(project), subproject)], alt_row))

    def clean_columns(self):
        self.clean_markers_column() if self.task_config.print_empty_columns else self.clean_empty_columns()

    def clean_markers_column(self):
        self.non_filtered_columns = [False if (c['name'] == MARKER_COLUMN_NAME and c['width'] == 0) else c for c in self.columns]
        self.columns = [c for c in self.columns if not (c['name'] == MARKER_COLUMN_NAME and c['width'] == 0)]

    def clean_empty_columns(self):
        self.non_filtered_columns = [c if c['width'] > 0 else False for c in self.columns]
        self.columns = [c for c in self.columns if c['width'] > 0]

    def resize_columns(self):
        cols, _ = self.listbox.size
        padding = (len(self.columns) - 1) * COLUMN_PADDING
        total_width = padding
        to_adjust= []
        for idx, column in enumerate(self.columns):
            width = column['width']
            total_width += width
            if width > REDUCE_COLUMN_WIDTH_LIMIT:
                to_adjust.append({'idx': idx, 'width': width})
        if total_width > cols:
            self.adjust_oversized_columns(total_width - cols, to_adjust)
            if to_adjust:
                # This is called recursively to account for cases when further
                # reduction is necessary because one or more column's reductions
                # were limited to REDUCE_COLUMN_WIDTH_LIMIT.
                self.resize_columns()

    def adjust_oversized_columns(self, reduce_by, to_adjust):
        to_adjust = list(map(lambda c: c.update({'ratio': (c['width'] - REDUCE_COLUMN_WIDTH_LIMIT) / c['width']}) or c, to_adjust))
        ratio_total = reduce(lambda acc, c: acc + c['ratio'], to_adjust, 0)
        to_adjust = list(map(lambda c: c.update({'percentage': c['ratio'] / ratio_total}) or c, to_adjust))
        for c in to_adjust:
            adjusted_width = c['width'] - math.ceil(reduce_by * c['percentage'])
            self.columns[c['idx']]['width'] = adjusted_width if adjusted_width > REDUCE_COLUMN_WIDTH_LIMIT else REDUCE_COLUMN_WIDTH_LIMIT

    def reconcile_column_width_for_label(self):
        for idx, column in enumerate(self.columns):
            label_len = len(column['label'])
            if column['width'] < label_len:
                self.columns[idx]['width'] = label_len

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

    def format_task_batch(self, partial, start_idx):
        return [SelectableRow(self.non_filtered_columns, obj, start_idx + idx, on_select=self.on_select) if isinstance(obj, TaskRow) else ProjectPlaceholderRow(self.columns, obj, start_idx + idx) for idx, obj in enumerate(partial)]

    def build_table(self):
        self.make_header()
        self.batcher = ListBatcher(self.rows, self.list_walker, batch_to_formatter=self.format_task_batch)
        _, rows = self.listbox.size
        self.batcher.add(rows)

    def make_header(self):
        columns = []
        if len(self.columns) > 0:
            last_column = self.columns[-1]
            columns = [self.make_header_column(column, column == last_column) for column in self.columns]
        columns.append(self.make_padding('list-header-column'))
        list_header = urwid.Columns(columns)
        self.header = urwid.AttrMap(list_header, 'list-header')

    def make_header_column(self, column, is_last, space_between=COLUMN_PADDING):
        padding_width = 0 if is_last else space_between
        total_width = column['width'] + padding_width
        column_content = urwid.AttrMap(urwid.Padding(urwid.Text(column['label'], align='left')), 'list-header-column')
        padding_content = self.make_padding(is_last and 'list-header-column' or 'list-header-column-separator')
        columns = urwid.Columns([(column['width'], column_content), (padding_width, padding_content)])
        return (total_width, columns)

    def make_padding(self, display_attr):
        return urwid.AttrMap(urwid.Padding(urwid.Text('')), display_attr)

    def rows_size_grew(self, data):
        _, old_rows = data['old_size']
        _, new_rows = data['new_size']
        if new_rows > old_rows:
            return new_rows - old_rows
        return 0

    def size_changed(self, data):
        self.update_header(data['new_size'])
        grew = self.rows_size_grew(data)
        if grew > 0:
            self.batcher.add(grew)

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

    def __init__(self, columns, row, position, *, on_select=None, space_between=COLUMN_PADDING):
        self.task = row.task
        self.uuid = row.uuid
        self.id = row.id
        self.alt_row = row.alt_row
        self.position = position

        self._columns = urwid.Columns([(column['width'], urwid.Text(row.data[idx], align=column['align'])) for idx, column in enumerate(columns) if column],
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

class ProjectPlaceholderRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' for a project placeholder row.
    """

    def __init__(self, columns, row, position, space_between=COLUMN_PADDING):
        self.uuid = None
        self.id = None
        self.alt_row = row.alt_row
        self.project = row.project
        self.placeholder = row.placeholder
        self.position = position
        self._columns = urwid.Columns([(column['width'], urwid.Text(row.placeholder if isinstance(column['formatter'], ProjectFormatter) else '', align=column['align'])) for column in columns], dividechars=space_between)

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

class TaskListBox(BaseListBox):
    """Maps task list shortcuts to default ListBox class.
    """

    def __init__(self, body, screen, event=None, request_reply=None, action_manager=None):
        # TODO: Any way to get the actual listbox size here? It doesn't seem
        # to be accessible before the first render() call.
        self.screen = screen
        self.size = self.screen.get_cols_rows()
        return super().__init__(body, event, request_reply, action_manager)

    def render(self, size, focus=False):
        if size != self.size:
            data = {
                'old_size': self.size,
                'new_size': size,
            }
            self.size = size
            self.event.emit('task-list:size:change', data)
        return super().render(size, focus)

    def keypress_down(self, size):
        self.event.emit('task-list:keypress:down', size)
        super().keypress_down(size)

    def keypress_page_down(self, size):
        self.event.emit('task-list:keypress:page_down', size)
        super().keypress_page_down(size)

    def keypress_end(self, size):
        self.event.emit('task-list:keypress:end', size)
        super().keypress_end(size)

    def keypress_focus_valign_center(self, size):
        self.event.emit('task-list:keypress:focus_valign_center', size)
        super().keypress_focus_valign_center(size)

    def set_focus_position(self, start_idx=0):
        for idx, widget in enumerate(self.body[start_idx:]):
            if widget.selectable():
                self.set_focus(start_idx + idx)
                return

    def focus_by_batch(self, match_callback, start_idx):
        end_idx = start_idx
        for idx, row in enumerate(self.body[start_idx:]):
            end_idx = idx + start_idx
            if match_callback(row):
                self.focus_position = end_idx
                return True, end_idx
        return False, end_idx

    def focus_by_batch_loop(self, match_callback, previous_idx=0):
        start_idx = 0
        while True:
            found, start_idx = self.focus_by_batch(match_callback, start_idx)
            complete = self.request_reply.request('task-table:batch:next')
            if found:
                return
            elif complete:
                found, end_idx = self.focus_by_batch(match_callback, start_idx)
                if not found:
                    self.set_focus_position(end_idx if previous_idx > end_idx else previous_idx)
                return

    def focus_by_task_id(self, task_id):
        def match_callback(row):
            return row.id == task_id
        self.focus_by_batch_loop(match_callback)

    def focus_by_task_uuid(self, uuid, previous_idx=0):
        def match_callback(row):
            return row.uuid == uuid
        self.focus_by_batch_loop(match_callback, previous_idx)

    def list_action_executed(self, size, key):
        data = {
            'size': size,
        }
        self.event.emit('task-list:keypress', data)
