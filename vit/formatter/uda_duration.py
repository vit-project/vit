from vit.formatter import String
from vit.util import unicode_len

class UdaDuration(String):
    def format(self, duration, task):
        if not duration:
            return self.markup_none(self.colorize())
        return (unicode_len(duration), self.markup_element(duration))
    def colorize(self, duration=None):
        return self.colorizer.uda_duration(self.column, duration)
