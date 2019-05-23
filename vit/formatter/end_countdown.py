from vit.formatter.end import End

class EndCountdown(End):
    def format(self, end, task):
        return self.countdown(end)
