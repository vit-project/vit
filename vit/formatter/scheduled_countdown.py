from vit.formatter.scheduled import Scheduled

class ScheduledCountdown(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.countdown(scheduled)
