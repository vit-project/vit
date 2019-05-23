from vit.formatter import String

class UdaDuration(String):
    def format(self, duration, task):
        if not duration:
            return self.markup_none(self.colorize())
        return (len(duration), self.markup_element(duration))
    def colorize(self, duration=None):
        return self.colorizer.uda_duration(self.column, duration)
