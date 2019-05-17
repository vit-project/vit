from vit.formatter.due import Due

class DueAge(Due):
    def format_datetime(self, due, task):
        return self.age(due)
