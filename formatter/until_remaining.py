from formatter.until import Until

class UntilRemaining(Until):
    def format(self, until, task):
        return self.remaining(until)
