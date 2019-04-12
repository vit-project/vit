from formatter.end import End

class EndCountdown(End):
    def format(self, dt):
        return self.countdown(dt)
