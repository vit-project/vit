from formatter.scheduled import Scheduled

class ScheduledCountdown(Scheduled):
    def format(self, dt):
        return self.countdown(dt)
