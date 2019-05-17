from vit.formatter.wait import Wait

class WaitRemaining(Wait):
    def format(self, wait, task):
        return self.remaining(wait)
