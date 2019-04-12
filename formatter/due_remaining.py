from formatter.due import Due

class DueRemaining(Due):
    def format(self, dt):
        return self.remaining(dt)
