from vit.formatter.scheduled import Scheduled

class ScheduledAge(Scheduled):
    def format_datetime(self, scheduled, task):
        return self.age(scheduled)
