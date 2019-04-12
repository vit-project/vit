from formatter.wait import Wait

class WaitRemaining(Wait):
    def format(self, dt):
        return self.remaining(dt)
