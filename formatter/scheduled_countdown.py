from formatter.scheduled import Scheduled

class ScheduledCountdown(Scheduled):
    def format(self, scheduled, task):
        return self.countdown(scheduled)
