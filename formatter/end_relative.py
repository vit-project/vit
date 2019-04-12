from formatter.end import End

class EndRelative(End):
    def format(self, dt):
        return self.relative(dt)
