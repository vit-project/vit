from vit.formatter.due import Due

class DueRelative(Due):
    def format_datetime(self, due, task):
        return self.relative(due)
