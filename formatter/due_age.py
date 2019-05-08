from formatter.due import Due

class DueAge(Due):
    def format_datetime(self, due):
        return self.age(due)
