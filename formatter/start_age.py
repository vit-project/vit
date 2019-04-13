from formatter.start import Start

class StartAge(Start):
    def format(self, start, task):
        return self.age(start)
