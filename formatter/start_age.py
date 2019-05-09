from formatter.start import Start

class StartAge(Start):
    def format_datetime(self, start):
        return self.age(start)
