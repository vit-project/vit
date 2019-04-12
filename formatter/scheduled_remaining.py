from formatter.scheduled import Scheduled

class ScheduledRemaining(Scheduled):
    def format(self, dt):
        return self.remaining(dt)
