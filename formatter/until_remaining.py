from formatter.until import Until

class UntilRemaining(Until):
    def format(self, dt):
        return self.remaining(dt)
