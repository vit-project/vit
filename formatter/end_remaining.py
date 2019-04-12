from formatter.end import End

class EndRemaining(End):
    def format(self, dt):
        return self.remaining(dt)
