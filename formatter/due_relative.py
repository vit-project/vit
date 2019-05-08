from formatter.due import Due

class DueRelative(Due):
    def format_datetime(self, due):
        return self.relative(due)
