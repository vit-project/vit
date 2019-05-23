from vit.formatter.urgency import Urgency

class UrgencyInteger(Urgency):
    def format(self, urgency, task):
        return "{0:.0f}".format(urgency)
