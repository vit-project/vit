from vit.formatter import Duration

class Recur(Duration):
    def colorize(self, recur):
        return self.colorizer.recurring(recur)
