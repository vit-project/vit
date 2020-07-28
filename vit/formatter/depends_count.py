from vit.formatter.depends import Depends

class DependsCount(Depends):
    def format_list(self, depends, task):
        return '[%d]' % len(self.filter_by_blocking_task_uuids(depends)) if depends else ''
