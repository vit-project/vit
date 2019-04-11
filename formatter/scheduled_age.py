from formatter.scheduled import Scheduled

class ScheduledAge(Scheduled):
    def format(self, dt):
        return self.age(dt)
