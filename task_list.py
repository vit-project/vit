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

    def __init__(self, task_config, on_select=None):
        self.task_config = task_config
        self.on_select = on_select
        self.formatter = formatter.Defaults(task_config)

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

    def set_column_metadata(self):
        for idx, column_formatter in enumerate(self.report['columns']):
            name, formatter_class = self.formatter.get(column_formatter)
            self.columns[name] = {
                'label': self.report['labels'][idx],
                'formatter': formatter_class,
                'width': 0,
            }

    def build_rows(self):
        for task in self.tasks:
            row_data = {}
            for column, metadata in list(self.columns.items()):
                current = metadata['width']
                formatted_value = metadata['formatter'](task, self.formatter).format(task[column])
                new = len(formatted_value) if formatted_value else 0
                if new > current and current < MAX_COLUMN_WIDTH:
                    self.columns[column]['width'] = new < MAX_COLUMN_WIDTH and new or MAX_COLUMN_WIDTH
                row_data[column] = formatted_value
            self.rows.append(TaskRow(task, row_data))

    def clean_empty_columns(self):
        self.columns = {c:m for c,m in list(self.columns.items()) if m['width'] > 0}

    def reconcile_column_width_for_label(self):
        for column, metadata in list(self.columns.items()):
            label_len = len(metadata['label'])
            if metadata['width'] < label_len:
                self.columns[column]['width'] = label_len

    def build_table(self):
        self.contents = [SelectableRow(self.columns, task, on_select=self.on_select) for task in self.rows]
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

