from vit.formatter.scheduled import Scheduled

class ScheduledRelative(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.relative(scheduled)
