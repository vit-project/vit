from formatter.until import Until

class UntilCountdown(Until):
    def format(self, dt):
        return self.countdown(dt)
