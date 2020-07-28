from vit.formatter.depends import Depends

class DependsIndicator(Depends):
    def format_list(self, depends, task):
        return self.formatter.indicator_dependency if self.filter_by_blocking_task_uuids(depends) else ''
