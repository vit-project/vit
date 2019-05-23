from vit.formatter import Number

class UdaNumeric(Number):
    def format(self, number, task):
        if number is None:
            return self.markup_none(self.colorize())
        number = str(number)
        return (len(number), self.markup_element(number))
    def colorize(self, number=None):
        return self.colorizer.uda_numeric(self.column, number)
