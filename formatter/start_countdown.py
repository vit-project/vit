from formatter.start import Start

class StartCountdown(Start):
    def format_datetime(self, start):
        return self.countdown(start)
