from vit.formatter.wait import Wait

class WaitAge(Wait):
    def format(self, wait, task):
        return self.age(wait)
