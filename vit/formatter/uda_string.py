from vit.formatter import String

class UdaString(String):
    def format(self, string, task):
        if not string:
            return self.markup_none(self.colorize())
        return (len(string), self.markup_element(string))
    def colorize(self, string=None):
        return self.colorizer.uda_string(self.column, string)
