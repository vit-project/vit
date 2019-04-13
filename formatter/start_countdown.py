from formatter.start import Start

class StartCountdown(Start):
    def format(self, start, task):
        return self.countdown(start)
