from formatter import DateTime

class Start(DateTime):
    def colorize(self, start):
        return self.colorizer.active(start)
