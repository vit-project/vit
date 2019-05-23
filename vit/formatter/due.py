from vit.formatter import DateTime

class Due(DateTime):
    def get_due_state(self, due, task):
        return self.formatter.get_due_state(due, task)

    def colorize(self, due, task):
        return self.colorizer.due(self.get_due_state(due, task))
