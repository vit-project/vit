from formatter.due import Due

class DueAge(Due):
    def format(self, due, task):
        return self.age(due)
