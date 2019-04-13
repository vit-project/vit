from formatter.until import Until

class UntilCountdown(Until):
    def format(self, until, task):
        return self.countdown(until)
