from vit.formatter import DateTime

class Scheduled(DateTime):
    def get_scheduled_state(self, scheduled, task):
        return self.formatter.get_scheduled_state(scheduled, task)

    def colorize(self, scheduled, task):
        return self.colorizer.scheduled(self.get_scheduled_state(scheduled, task))
