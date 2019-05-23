from vit.formatter.until import Until

class UntilJulian(Until):
    def format_datetime(self, until, task):
        return self.julian(until)
