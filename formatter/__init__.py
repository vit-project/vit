from importlib import import_module
import datetime
from tzlocal import get_localzone

import uda

class Defaults(object):
    def __init__(self, config):
        self.config = config
        self.report = self.config.translate_date_markers(config.subtree('dateformat.report'))
        self.annotation = self.config.translate_date_markers(config.subtree('dateformat.annotation'))

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

class Formatter(object):
    def __init__(self, task, defaults, **kwargs):
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

    def format(self, dt):
        return dt.strftime(self.custom_formatter or self.defaults.report) if dt else ''

    def seconds_to_age(self, seconds):
        if seconds <= 60:
            return '%ds' % seconds
        elif seconds <= 3600:
            return '%dm' % (seconds // 60)
        elif seconds <= 86400:
            return '%dh' % (seconds // 3600)
        elif seconds <= 604800:
            return '%dd' % (seconds // 86400)
        elif seconds <= 7257600:
            return '%dw' % (seconds // 604800)
        elif seconds <= 31536000:
            return '%dmo' % (seconds // 2592000)
        else:
            return '%dy' % (seconds // 31536000)

    def age(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        seconds = (now - dt).total_seconds()
        return self.seconds_to_age(seconds)

    def countdown(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.seconds_to_age(seconds)

class List(Formatter):
    def format(self, obj):
        return ','.join(obj) if obj else ''
