from formatter.until import Until

class UntilRelative(Until):
    def format(self, until, task):
        return self.relative(until)
