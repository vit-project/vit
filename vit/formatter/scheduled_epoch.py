from vit.formatter.scheduled import Scheduled

class ScheduledEpoch(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.epoch(scheduled)
