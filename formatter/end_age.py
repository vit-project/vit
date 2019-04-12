from formatter.end import End

class EndAge(End):
    def format(self, dt):
        return self.age(dt)
