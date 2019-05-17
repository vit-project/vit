from vit.formatter.until import Until

class UntilRelative(Until):
    def format_datetime(self, until, task):
        return self.relative(until)
