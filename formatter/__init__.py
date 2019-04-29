from importlib import import_module
import datetime
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

class Formatter(object):
    def __init__(self, report, defaults, **kwargs):
        self.report = report
        self.defaults = defaults
        self.colorizer = self.defaults.task_colorizer

    def format(self, obj, task):
        return str(obj) if obj else ''

    def markup_element(self, obj):
        return (self.colorize(obj), obj)

class Marker(Formatter):
    def __init__(self, report, defaults, report_marker_columns):
        self.columns = report_marker_columns
        super().__init__(report, defaults)
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
    def __init__(self, report, defaults, custom_formatter=None):
        self.custom_formatter = custom_formatter
        super().__init__(report, defaults)

    def format(self, dt, task):
        return dt.strftime(self.custom_formatter or self.defaults.report) if dt else ''

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
        now = datetime.datetime.now(get_localzone())
        seconds = (now - dt).total_seconds()
        return self.format_duration_vague(seconds)

    def countdown(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def relative(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def remaining(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

class List(Formatter):
    def format(self, obj, task):
        return ','.join(obj) if obj else ''
