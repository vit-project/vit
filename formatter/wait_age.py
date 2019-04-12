from formatter.wait import Wait

class WaitAge(Wait):
    def format(self, dt):
        return self.age(dt)
