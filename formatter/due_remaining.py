from formatter.due import Due

class DueRemaining(Due):
    def format_datetime(self, due):
        return self.remaining(due)
