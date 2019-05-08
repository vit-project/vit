from formatter import DateTime

class Due(DateTime):
    def get_due_state(self, due):
        return self.defaults.get_due_state(due)

    def colorize(self, due):
        return self.colorizer.due(self.get_due_state(due))
