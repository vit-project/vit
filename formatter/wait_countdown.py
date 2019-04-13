from formatter.wait import Wait

class WaitCountdown(Wait):
    def format(self, wait, task):
        return self.countdown(wait)
