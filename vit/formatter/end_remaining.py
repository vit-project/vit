from vit.formatter.end import End

class EndRemaining(End):
    def format(self, end, task):
        return self.remaining(end)
