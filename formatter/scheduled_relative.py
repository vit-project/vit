from formatter.scheduled import Scheduled

class ScheduledRelative(Scheduled):
    def format(self, scheduled, task):
        return self.relative(scheduled)
