from vit.formatter.wait import Wait

class WaitEpoch(Wait):
    def format(self, wait, task):
        return self.epoch(wait)
