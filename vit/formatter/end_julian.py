from vit.formatter.end import End

class EndJulian(End):
    def format(self, end, task):
        return self.julian(end)
