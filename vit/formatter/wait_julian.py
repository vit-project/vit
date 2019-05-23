from vit.formatter.wait import Wait

class WaitJulian(Wait):
    def format(self, wait, task):
        return self.julian(wait)
