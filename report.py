from operator import itemgetter
from collections import OrderedDict

import formatter

MAX_COLUMN_WIDTH = 60

class TaskTable(object):

    def __init__(self, task_config, report, tasks):
        self.report = report
        self.tasks = tasks
        self.formatter_defaults = formatter.Defaults(task_config)
        self.columns = OrderedDict()
        self.rows = []
        self.sort()
        self.set_column_metadata()
        self.build_rows()
        # TODO: Make this optional based on Taskwarrior config setting.
        self.clean_empty_columns()
        self.reconcile_column_width_for_label()

    def sort(self):
        for column, order, collate in reversed(self.report['sort']):
            if order and order == 'descending':
                self.tasks = sorted(self.tasks, key=itemgetter(column), reverse=True)
            else:
                self.tasks = sorted(self.tasks, key=itemgetter(column))

    def set_column_metadata(self):
        for idx, column_formatter in enumerate(self.report['columns']):
            parts = column_formatter.split('.')
            name = parts[0]
            formatter_class_name = ''.join([p.capitalize() for p in parts])
            formatter_class = getattr(formatter, formatter_class_name)
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
                formatted_value = metadata['formatter'](task, self.formatter_defaults).format(task[column])
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

class TaskRow():
    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.uuid = self.task['uuid']
