from formatter import DateTime

class Due(DateTime):
    def get_due_state(self, dt):
        return self.defaults.get_due_state(dt)

    def colorize(self, dt):
        return self.colorizer.due(self.get_due_state(dt))
