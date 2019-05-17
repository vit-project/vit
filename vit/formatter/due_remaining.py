from vit.formatter.due import Due

class DueRemaining(Due):
    def format_datetime(self, due, task):
        return self.remaining(due)
