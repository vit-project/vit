from formatter.scheduled import Scheduled

class ScheduledAge(Scheduled):
    def format(self, scheduled, task):
        return self.age(scheduled)
