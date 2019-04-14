from importlib import import_module
import datetime
from tzlocal import get_localzone

import uda

class Defaults(object):
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
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
            return project_parts[0]
        else:
            subproject = project_parts.pop()
            space_padding = (len(project_parts) * 2) - 1
            return '%s%s %s' % (' ' * space_padding, u'\u21aa', subproject)

class Formatter(object):
    def __init__(self, report, defaults, **kwargs):
        self.report = report
        self.defaults = defaults

    def format(self, obj, task):
        return str(obj) if obj else ''

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

    def seconds_to_age(self, seconds):
        test = -seconds if seconds < 0 else seconds
        result = ''
        if test <= 60:
            result = '%ds' % seconds
        elif test <= 3600:
            result = '%dm' % (seconds // 60)
        elif test <= 86400:
            result = '%dh' % (seconds // 3600)
        elif test <= 604800:
            result = '%dd' % (seconds // 86400)
        elif test <= 7257600:
            result = '%dw' % (seconds // 604800)
        elif test <= 31536000:
            result = '%dmo' % (seconds // 2592000)
        else:
            result = '%dy' % (seconds // 31536000)
        return result

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

    def relative(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        seconds = (dt - now).total_seconds()
        return self.seconds_to_age(seconds)

    def remaining(self, dt):
        if dt == None:
            return ''
        now = datetime.datetime.now(get_localzone())
        if dt < now:
            return ''
        seconds = (dt - now).total_seconds()
        return self.seconds_to_age(seconds)

class List(Formatter):
    def format(self, obj, task):
        return ','.join(obj) if obj else ''
