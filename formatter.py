current_module = __import__(__name__)
import uda

class Defaults(object):
    def __init__(self, config):
        self.config = config
        self.report = self.translate_date_markers(config.subtree('dateformat.report'))
        self.annotation = self.translate_date_markers(config.subtree('dateformat.annotation'))

    def get(self, column_formatter):
        parts = column_formatter.split('.')
        name = parts[0]
        formatter_class_name = ''.join([p.capitalize() for p in parts])
        try:
            formatter_class = getattr(current_module, formatter_class_name)
            return name, formatter_class
        except AttributeError:
            uda_metadata = uda.get(name, self.config)
            if uda_metadata:
                uda_type = uda_metadata['type'] if 'type' in uda_metadata else 'string'
                formatter_class_name = 'Uda%s' % uda_type.capitalize()
                try:
                    formatter_class = getattr(current_module, formatter_class_name)
                    return name, formatter_class
                except AttributeError:
                    pass
        return name, Formatter

    def translate_date_markers(self, string):
        # TODO:
        return string

class Formatter(object):
    def __init__(self, task, defaults):
        self.task = task
        self.defaults = defaults

    def format(self, number):
        return str(number) if number else ''

class Number(Formatter):
    pass

class String(Formatter):
    def format(self, string):
        return string if string else ''

class DateTime(Formatter):
    def format(self, datetime):
        return datetime.strftime('%Y-%m-%d') if datetime else ''

class List(Formatter):
    def format(self, obj):
        return ','.join(obj) if obj else ''

class Id(Number):
    pass

class Project(String):
    pass

class Description(String):
    pass

class DescriptionCount(String):
    def format(self, string):
        if self.task['annotations']:
            return "%s [%d]" % (string, len(self.task['annotations']))
        else:
            return string

class Tags(List):
    pass

class TagsCount(Formatter):
    def format(self, string):
        if self.task['tags'] and len(self.task['tags']) > 0:
            return "[%d]" % len(self.task['tags'])
        else:
            return ''

class Scheduled(DateTime):
    pass

class Due(DateTime):
    pass

class UdaString(String):
    pass

class UdaNumeric(Number):
    pass

class UdaDate(DateTime):
    pass

class UdaDuration(String):
    pass
