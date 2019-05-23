from vit.formatter.until import Until

class UntilAge(Until):
    def format_datetime(self, until, task):
        return self.age(until)
