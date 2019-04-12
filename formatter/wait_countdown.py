from formatter.wait import Wait

class WaitCountdown(Wait):
    def format(self, dt):
        return self.countdown(dt)
