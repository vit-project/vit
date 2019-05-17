from vit.formatter.until import Until

class UntilEpoch(Until):
    def format_datetime(self, until, task):
        return self.epoch(until)
