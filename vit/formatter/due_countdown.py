from vit.formatter.due import Due

class DueCountdown(Due):
    def format_datetime(self, due, task):
        return self.countdown(due)
