from formatter.until import Until

class UntilAge(Until):
    def format(self, until, task):
        return self.age(until)
