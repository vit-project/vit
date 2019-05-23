from vit.formatter.scheduled import Scheduled

class ScheduledIso(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.iso(scheduled)
