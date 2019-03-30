class Defaults(object):
    def __init__(self, config):
        self.report = self.translate_date_markers(config.subtree('dateformat.report', walk_subtree=True))
        self.annotation = self.translate_date_markers(config.subtree('dateformat.annotation', walk_subtree=True))
    def translate_date_markers(self, string):
        # TODO:
        return string

class Formatter(object):
    def __init__(self, task, defaults):
        self.task = task
        self.defaults = defaults

class Number(Formatter):
    def format(self, number):
        return str(number) if number else ''

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

class Scheduled(DateTime):
    pass

class Due(DateTime):
    pass
