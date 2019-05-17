from vit.formatter import Number

class Urgency(Number):
    def format(self, urgency, task):
        return "{0:.2f}".format(urgency)
