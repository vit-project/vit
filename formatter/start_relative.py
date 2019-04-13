from formatter.start import Start

class StartRelative(Start):
    def format(self, start, task):
        return self.relative(start)
