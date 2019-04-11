from formatter.due import Due

class DueAge(Due):
    def format(self, dt):
        return self.age(dt)
