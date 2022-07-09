from vit.formatter import String
from vit.util import unicode_len

class UdaString(String):
    def format(self, string, task):
        if not string:
            return self.markup_none(self.colorize())
        return (unicode_len(string), self.markup_element(string))
    def colorize(self, string=None):
        return self.colorizer.uda_string(self.column, string)
