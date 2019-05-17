from vit.formatter.depends import Depends

class DependsCount(Depends):
    def format_list(self, depends, task):
        return '[%d]' % len(depends) if depends else ''
