from importlib import import_module

from functools import reduce

import datetime

import uda

# strftime() works differently on Windows, test here.
test_datetime = datetime.datetime(1900, 1, 1)
NO_PAD_FORMAT_CODE = '-' if test_datetime.strftime('%-d') == '1' else '#' if test_datetime.strftime('%#d') == '1' else ''

DATE_FORMAT_MAPPING = {
    'm': '%%%sm' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit month number, eg '1', '12'
    'M': '%m',                           # 2 digit month number, eg '01', '12'
    'd': '%%%sd' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit day of month number¸ eg '1', '12'
    'D': '%d',                           # 2 digit day of month number, eg '01', '30'
    'y': '%y',                           # 2 digit year, eg '12', where the century is assumed to be '20', therefore '2012'
    'Y': '%Y',                           # 4 digit year, eg '2015'
    'h': '%%%sH' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit hours, eg '1', '23'
    'H': '%H',                           # 2 digit hours, eg '01', '23'
    'n': '%%%sM' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit minutes, eg '1', '59'
    'N': '%M',                           # 2 digit minutes, eg '01', '59'
    's': '%%%sS' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit seconds, eg '1', '59'
    'S': '%S',                           # 2 digit seconds, eg '01', '59'
    'v': '%%%sU' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit week number, eg '1', '52'
    'V': '%U',                           # 2 digit week number, eg '01', '52'
    'a': '%a',                           # 3-character English day name abbreviation, eg 'mon', 'tue'
    'A': '%A',                           # Complete English day name, eg 'monday', 'tuesday'
    'b': '%b',                           # 3-character English month name abbreviation, eg 'jan', 'feb'
    'B': '%B',                           # Complete English month name, eg 'january', 'february'
    'j': '%%%sj' % NO_PAD_FORMAT_CODE,   # 1, 2 or 3 digit day-of-year number, sometimes referred to as a Julian date, eg '1', '11', or '365'
    'J': '%j',                           # 3 digit day of year number, sometimes referred to as a Julian date, eg '001', '011', or '365'
}

class Defaults(object):
    def __init__(self, config):
        self.config = config
        self.report = self.translate_date_markers(config.subtree('dateformat.report'))
        self.annotation = self.translate_date_markers(config.subtree('dateformat.annotation'))

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
            uda_metadata = uda.get(name, self.config)
            if uda_metadata:
                uda_type = uda_metadata['type'] if 'type' in uda_metadata else 'string'
                formatter_class = self.get_formatter_class(['uda', uda_type])
                if formatter_class:
                    return name, formatter_class
        return name, Formatter

    def translate_date_markers(self, string):
        return reduce(lambda accum, code: accum.replace(code[0], code[1]), list(DATE_FORMAT_MAPPING.items()), string)

class Formatter(object):
    def __init__(self, task, defaults):
        self.task = task
        self.defaults = defaults

    def format(self, number):
        return str(number) if number else ''

class Number(Formatter):
    pass

class String(Formatter):
    pass

class Duration(Formatter):
    pass

class DateTime(Formatter):
    def __init__(self, task, defaults, custom_formatter=None):
        self.custom_formatter = custom_formatter
        super().__init__(task, defaults)

    def format(self, datetime):
        return datetime.strftime(self.custom_formatter or self.defaults.report) if datetime else ''

class List(Formatter):
    def format(self, obj):
        return ','.join(obj) if obj else ''
