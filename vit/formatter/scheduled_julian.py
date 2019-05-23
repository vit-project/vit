from vit.formatter.scheduled import Scheduled

class ScheduledJulian(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.julian(scheduled)
