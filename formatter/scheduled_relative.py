from formatter.scheduled import Scheduled

class ScheduledRelative(Scheduled):
    def format(self, dt):
        return self.relative(dt)
