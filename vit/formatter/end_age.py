from vit.formatter.end import End

class EndAge(End):
    def format(self, end, task):
        return self.age(end)
