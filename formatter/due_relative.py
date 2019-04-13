from formatter.due import Due

class DueRelative(Due):
    def format(self, due, task):
        return self.relative(due)
