from formatter.due import Due

class DueCountdown(Due):
    def format_datetime(self, due):
        return self.countdown(due)
