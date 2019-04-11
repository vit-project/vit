from formatter.until import Until

class UntilAge(Until):
    def format(self, dt):
        return self.age(dt)
