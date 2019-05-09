from formatter.start import Start

class StartRemaining(Start):
    def format_datetime(self, start):
        return self.remaining(start)
