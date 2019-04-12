from formatter.start import Start

class StartRemaining(Start):
    def format(self, dt):
        return self.remaining(dt)
