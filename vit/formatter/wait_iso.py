from vit.formatter.wait import Wait

class WaitIso(Wait):
    def format(self, wait, task):
        return self.iso(wait)
