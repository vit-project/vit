from formatter.wait import Wait

class WaitRelative(Wait):
    def format(self, dt):
        return self.relative(dt)
