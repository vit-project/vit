from formatter.due import Due

class DueCountdown(Due):
    def format(self, dt):
        return self.countdown(dt)
