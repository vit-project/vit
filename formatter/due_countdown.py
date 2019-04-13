from formatter.due import Due

class DueCountdown(Due):
    def format(self, due, task):
        return self.countdown(due)
