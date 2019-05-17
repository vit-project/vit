import math
from importlib import import_module
from datetime import datetime, timedelta
from tzlocal import get_localzone
from pytz import timezone

from vit import util
from vit import uda

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

INDICATORS = [
    'active',
    'dependency',
    'recurrence',
    'tag',
]
UDA_DEFAULT_INDICATOR = 'U'

DEFAULT_DESCRIPTION_TRUNCATE_LEN=20

class Defaults(object):
    def __init__(self, loader, config, task_config, markers, task_colorizer):
        self.loader = loader
        self.config = config
        self.task_config = task_config
        self.markers = markers
        self.task_colorizer = task_colorizer
        self.report = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.report'))
        self.annotation = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.annotation'))
        self.description_truncate_len = DEFAULT_DESCRIPTION_TRUNCATE_LEN
        self.zone = get_localzone()
        self.epoch_datetime = datetime(1970, 1, 1, tzinfo=timezone('UTC'))
        self.due_days = int(self.task_config.subtree('due'))
        self.none_label = config.get('color', 'none_label')
        self.build_indicators()

    def build_indicators(self):
        for indicator in INDICATORS:
            label = self.task_config.subtree('%s.indicator' % indicator)
            setattr(self, 'indicator_%s' % indicator, label)
        self.indicator_uda = {}
        for uda_name in uda.get_configured(self.task_config).keys():
            label = self.task_config.subtree('uda.%s.indicator' % uda_name) or UDA_DEFAULT_INDICATOR
            self.indicator_uda[uda_name] = label

    def get_module_class_from_parts(self, parts):
        formatter_module_name = '_'.join(parts)
        formatter_class_name = util.file_to_class_name(formatter_module_name)
        return formatter_module_name, formatter_class_name

    def get_user_formatter_class(self, parts):
        formatter_module_name, formatter_class_name = self.get_module_class_from_parts(parts)
        return self.loader.load_user_class('formatter', formatter_module_name, formatter_class_name)

    def get_formatter_class(self, parts):
        formatter_module_name, formatter_class_name = self.get_module_class_from_parts(parts)
        try:
            formatter_module = import_module('vit.formatter.%s' % formatter_module_name)
            formatter_class = getattr(formatter_module, formatter_class_name)
            return formatter_class
        except ImportError:
            return None

    def get(self, column_formatter):
        parts = column_formatter.split('.')
        name = parts[0]

        formatter_class = self.get_user_formatter_class(parts)
        if formatter_class:
            return name, formatter_class

        formatter_class = self.get_formatter_class(parts)
        if formatter_class:
            return name, formatter_class

        uda_metadata = uda.get(name, self.task_config)
        if uda_metadata:
            is_indicator = parts[-1] == 'indicator'
            if is_indicator:
                formatter_class = self.get_formatter_class(['uda', 'indicator'])
                return name, formatter_class
            else:
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

    def get_due_state(self, due, task):
        if util.task_pending(task):
            if due < self.now:
                return 'overdue'
            elif due <= self.end_of_day:
                return 'due.today'
            elif due < self.due_soon:
                return 'due'
        return None

    def get_active_state(self, start, task):
        end = task['end']
        return util.task_pending(task) and start and start <= self.now and (not end or end > self.now)

    def get_scheduled_state(self, scheduled, task):
        return scheduled and not util.task_completed(task)

    def get_until_state(self, until, task):
        return until and not util.task_completed(task)

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
    def format(self, obj, task):
        if not obj:
            return self.empty()
        formatted_duration = self.format_duration(obj)
        return (len(formatted_duration), self.markup_element(obj, formatted_duration))

    def format_duration(self, obj):
        return obj

    def markup_element(self, obj, formatted_duration):
        return (self.colorize(obj), formatted_duration)

class DateTime(Formatter):
    def __init__(self, column, report, defaults, **kwargs):
        self.custom_formatter = None if not 'custom_formatter' in kwargs else kwargs['custom_formatter']
        super().__init__(column, report, defaults)

    def format(self, dt, task):
        if not dt:
            return self.empty()
        formatted_date = self.format_datetime(dt, task)
        return (len(formatted_date), self.markup_element(dt, formatted_date, task))

    def format_datetime(self, dt, task):
        return dt.strftime(self.custom_formatter or self.defaults.report)

    def markup_element(self, dt, formatted_date, task):
        return (self.colorize(dt, task), formatted_date)

    def colorize(self, dt, task):
        return None

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

    def epoch(self, dt):
        if dt == None:
            return ''
        return str(round((dt - self.defaults.epoch_datetime).total_seconds()))

    # Taken from https://github.com/dannyzed/julian
    def julian(self, dt):
        if dt == None:
            return ''
        a = math.floor((14-dt.month)/12)
        y = dt.year + 4800 - a
        m = dt.month + 12*a - 3
        jdn = dt.day + math.floor((153*m + 2)/5) + 365*y + math.floor(y/4) - math.floor(y/100) + math.floor(y/400) - 32045
        jd = jdn + (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400 + dt.microsecond / 86400000000
        return str(jd)

    def iso(self, dt):
        if dt == None:
            return ''
        dt = dt.replace(tzinfo=timezone('UTC'))
        return dt.isoformat()

class List(Formatter):

    def format(self, obj, task):
        if not obj:
            return self.empty()
        formatted = self.format_list(obj, task)
        return (len(formatted), self.markup_element(obj, formatted))

    def markup_element(self, obj, formatted):
        return (self.colorize(obj), formatted)

    def format_list(self, obj, task):
        return ','.join(obj) if obj else ''
