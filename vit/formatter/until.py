from vit.formatter import DateTime

class Until(DateTime):
    def get_until_state(self, until, task):
        return self.formatter.get_until_state(until, task)

    def colorize(self, until, task):
        return self.colorizer.until(self.get_until_state(until, task))
