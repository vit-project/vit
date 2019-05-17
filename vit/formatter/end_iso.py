from vit.formatter.end import End

class EndIso(End):
    def format(self, end, task):
        return self.iso(end)
