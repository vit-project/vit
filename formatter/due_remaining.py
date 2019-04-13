from formatter.due import Due

class DueRemaining(Due):
    def format(self, due, task):
        return self.remaining(due)
