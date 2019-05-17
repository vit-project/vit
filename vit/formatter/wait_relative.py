from vit.formatter.wait import Wait

class WaitRelative(Wait):
    def format(self, wait, task):
        return self.relative(wait)
