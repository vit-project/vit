from vit.formatter.end import End

class EndEpoch(End):
    def format(self, end, task):
        return self.epoch(end)
