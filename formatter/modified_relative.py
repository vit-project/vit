from formatter.modified import Modified

class ModifiedRelative(Modified):
    def format(self, dt):
        return self.relative(dt)
