from vit.formatter.until import Until

class UntilRemaining(Until):
    def format_datetime(self, until, task):
        return self.remaining(until)
