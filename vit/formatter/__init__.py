import math
from datetime import datetime
from pytz import timezone

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

class Formatter(object):
    def __init__(self, column, report, formatter_base, blocking_task_uuids, **kwargs):
        self.column = column
        self.report = report
        self.formatter = formatter_base
        self.colorizer = self.formatter.task_colorizer
        self.blocking_task_uuids = blocking_task_uuids

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
            return (len(self.formatter.none_label), (color, self.formatter.none_label))
        else:
            return self.empty()

    def colorize(self, obj):
        return None

    def filter_by_blocking_task_uuids(self, depends):
        return [ task for task in depends if task['uuid'] in self.blocking_task_uuids ]

class Marker(Formatter):
    def __init__(self, report, defaults, report_marker_columns, blocking_task_uuids):
        super().__init__(None, report, defaults, blocking_task_uuids)
        self.columns = report_marker_columns
        self.labels = self.formatter.markers.labels
        self.udas = self.formatter.markers.udas
        self.require_color = self.formatter.markers.require_color
        self.set_column_attrs()

    def set_column_attrs(self):
        any(setattr(self, 'mark_%s' % column, column in self.columns) for column in self.formatter.markers.markable_columns)

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
    def __init__(self, column, report, defaults, blocking_task_uuids, **kwargs):
        self.custom_formatter = None if not 'custom_formatter' in kwargs else kwargs['custom_formatter']
        super().__init__(column, report, defaults, blocking_task_uuids)

    def format(self, dt, task):
        if not dt:
            return self.empty()
        formatted_date = self.format_datetime(dt, task)
        return (len(formatted_date), self.markup_element(dt, formatted_date, task))

    def format_datetime(self, dt, task):
        return dt.strftime(self.custom_formatter or self.formatter.report)

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
        now = datetime.now(self.formatter.zone)
        seconds = (now - dt).total_seconds()
        return self.format_duration_vague(seconds)

    def countdown(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.formatter.zone)
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def relative(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.formatter.zone)
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def remaining(self, dt):
        if dt == None:
            return ''
        now = datetime.now(self.formatter.zone)
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.format_duration_vague(seconds)

    def epoch(self, dt):
        if dt == None:
            return ''
        return str(round((dt - self.formatter.epoch_datetime).total_seconds()))

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
