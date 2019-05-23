from vit.formatter.end import End

class EndRelative(End):
    def format(self, end, task):
        return self.relative(end)
