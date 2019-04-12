from formatter.start import Start

class StartRelative(Start):
    def format(self, dt):
        return self.relative(dt)
