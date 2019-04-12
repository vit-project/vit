from formatter.until import Until

class UntilRelative(Until):
    def format(self, dt):
        return self.relative(dt)
