from vit.formatter.scheduled import Scheduled

class ScheduledRemaining(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.remaining(scheduled)
