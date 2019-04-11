from formatter.start import Start

class StartAge(Start):
    def format(self, dt):
        return self.age(dt)
