from formatter.start import Start

class StartRemaining(Start):
    def format(self, start, task):
        return self.remaining(start)
