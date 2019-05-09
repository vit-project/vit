from formatter.depends import Depends

class DependsIndicator(Depends):
    def format_list(self, depends, task):
        return 'D' if depends else ''
