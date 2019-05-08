from importlib import import_module
from datetime import datetime, timedelta
from tzlocal import get_localzone

import uda

TIME_UNIT_MAP = {
    'seconds': {
        'label': 's',
        'divisor': 1,
        'threshold': 60,
     },
    'minutes': {
        'label': 'm',
        'divisor': 60,
        'threshold': 3600,
     },
    'hours': {
        'label': 'h',
        'divisor': 3600,
        'threshold': 86400,
     },
    'days': {
        'label': 'd',
        'divisor': 86400,
        'threshold': 86400 * 14,
     },
    'weeks': {
        'label': 'w',
        'divisor': 86400 * 7,
        'threshold': 86400 * 90,
     },
    'months': {
        'label': 'mo',
        'divisor': 86400 * 30,
        'threshold': 86400 * 365,
     },
    'years': {
        'label': 'y',
        'divisor': 86400 * 365,
     },
}

class Defaults(object):
    def __init__(self, config, task_config, markers, task_colorizer):
        self.config = config
        self.task_config = task_config
        self.markers = markers
        self.task_colorizer = task_colorizer
        self.report = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.report'))
        self.annotation = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.annotation'))
        self.zone = get_localzone()
        self.due_days = int(self.task_config.subtree('due'))
        self.none_label = config.get('color', 'none_label')

    def get_formatter_class(self, parts):
        formatter_module_name = '_'.join(parts)
        formatter_class_name = ''.join([p.capitalize() for p in parts])
        try:
            formatter_module = import_module('formatter.%s' % formatter_module_name)
        except ImportError:
            return None
        formatter_class = getattr(formatter_module, formatter_class_name)
        return formatter_class

    def get(self, column_formatter):
        parts = column_formatter.split('.')
        name = parts[0]
        formatter_class = self.get_formatter_class(parts)
        if formatter_class:
            return name, formatter_class
        else:
            uda_metadata = uda.get(name, self.task_config)
            if uda_metadata:
                uda_type = uda_metadata['type'] if 'type' in uda_metadata else 'string'
                formatter_class = self.get_formatter_class(['uda', uda_type])
                if formatter_class:
                    return name, formatter_class
        return name, Formatter

    def format_subproject_indented(self, project_parts):
        if len(project_parts) == 1:
            subproject = project_parts[0]
            return (len(subproject), '', '', subproject)
        else:
            subproject = project_parts.pop()
            space_padding = (len(project_parts) * 2) - 1
            indicator = u'\u21aa '
            width = space_padding + len(indicator) + len(subproject)
            return (width, ' ' * space_padding , indicator, subproject)

    def recalculate_due_datetimes(self):
        self.now = datetime.now(self.zone)
        # NOTE: For some reason using self.zone for the tzinfo below results
        # in the tzinfo object having a zone of 'LMT', which is wrong. Using
        # the tzinfo associated with self.now returns the correct value, no
        # idea why this glitch happens.
        self.end_of_day = datetime(self.now.year, self.now.month, self.now.day, 23, 59, 59, tzinfo=self.now.tzinfo)
        self.due_soon = self.end_of_day + timedelta(days=self.due_days)

    def get_due_state(self, due):
        if due < self.now:
            return 'overdue'
        elif due <= self.end_of_day:
            return 'due.today'
        elif due < self.due_soon:
            return 'due'
        return None

class Formatter(object):
    def __init__(self, column, report, defaults, **kwargs):
        self.column = column
        self.report = report
        self.defaults = defaults
        self.colorizer = self.defaults.task_colorizer

    def format(self, obj, task):
        if not obj:
            return self.empty()
        obj = str(obj)
        return (len(obj), self.markup_element(obj))

    def empty(self):
        return (0, '')

    def markup_element(self, obj):
        return (self.colorize(obj), obj)

    def markup_none(self, color):
        if color:
            return (len(self.defaults.none_label), (color, self.defaults.none_label))
        else:
            return self.empty()

    def colorize(self, obj):
        return None

class Marker(Formatter):
    def __init__(self, report, defaults, report_marker_columns, blocking_task_uuids):
        super().__init__(None, report, defaults)
        self.columns = report_marker_columns
        self.blocking_tasks = blocking_task_uuids
        self.labels = self.defaults.markers.labels
        self.udas = self.defaults.markers.udas
        self.require_color = self.defaults.markers.require_color
        self.set_column_attrs()

    def set_column_attrs(self):
        any(setattr(self, 'mark_%s' % column, column in self.columns) for column in self.defaults.markers.markable_columns)

class Number(Formatter):
    pass

class String(Formatter):
    pass

class Duration(Formatter):
    pass

class DateTime(Formatter):
    def __init__(self, column, report, defaults, **kwargs):
        self.custom_formatter = None if not 'custom_formatter' in kwargs else kwargs['custom_formatter']
        super().__init__(column, report, defaults)

    def format(self, dt, task):
        if not dt:
            return self.empty()
        formatted_date = self.format_datetime(dt)
        return (len(formatted_date), self.markup_element(dt, formatted_date))

    def format_datetime(self, dt):
        return dt.strftime(self.custom_formatter or self.defaults.report)

    def markup_element(self, dt, formatted_date):
        return (self.colorize(dt), formatted_date)

    def format_duration_vague(self, seconds):
        test = seconds
        sign = ''
        unit = 'seconds'
        if seconds < 0:
            test = -seconds
            sign = '-'
        if test <= TIME_UNIT_MAP['seconds']['threshold']:
            # Handled by defaults
            pass
        elif test <= TIME_UNIT_MAP['minutes']['threshold']:
            unit = 'minutes'
        elif test <= TIME_UNIT_MAP['hours']['threshold']:
            unit = 'hours'
        elif test <= TIME_UNIT_MAP['days']['threshold']:
            unit = 'days'
        elif test <= TIME_UNIT_MAP['weeks']['threshold']:
            unit = 'weeks'
        elif test <= TIME_UNIT_MAP['months']['threshold']:
            unit = 'months'
        else:
            unit = 'years'
        age = test // TIME_UNIT_MAP[unit]['divisor']
        return '%s%d%s' % (sign, age, TIME_UNIT_MAP[unit]['label'])

    def age(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.defaults.zone)
        seconds = (now - dt).total_seconds()
        return self.format_duration_vague(seconds)

    def countdown(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.defaults.zone)
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def relative(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.defaults.zone)
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def remaining(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.defaults.zone)
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

class List(Formatter):
    def format(self, obj, task):
        return ','.join(obj) if obj else ''
