from formatter import Number

class Urgency(Number):
    def format(self, obj):
        return "{0:.2f}".format(obj)
