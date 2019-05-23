from vit.formatter.until import Until

class UntilCountdown(Until):
    def format_datetime(self, until, task):
        return self.countdown(until)
