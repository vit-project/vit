from formatter.start import Start

class StartCountdown(Start):
    def format(self, dt):
        return self.countdown(dt)
