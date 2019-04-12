from formatter.modified import Modified

class ModifiedRemaining(Modified):
    def format(self, dt):
        return self.remaining(dt)
