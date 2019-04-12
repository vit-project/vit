from formatter.modified import Modified

class ModifiedAge(Modified):
    def format(self, dt):
        return self.age(dt)
