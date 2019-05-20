from vit.formatter import Formatter

class UdaIndicator(Formatter):
    def format(self, value, task):
        if not value:
            return self.markup_none(self.colorize())
        else:
            indicator = self.formatter.indicator_uda[self.column]
            return (len(indicator), (self.colorize(value), indicator))

    def colorize(self, value=None):
        return self.colorizer.uda_indicator(self.column, value)
