from formatter.modified import Modified

class ModifiedCountdown(Modified):
    def format(self, dt):
        return self.countdown(dt)
