from formatter.scheduled import Scheduled

class ScheduledRemaining(Scheduled):
    def format(self, scheduled, task):
        return self.remaining(scheduled)
