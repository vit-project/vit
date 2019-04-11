from formatter.urgency import Urgency

class UrgencyInteger(Urgency):
    def format(self, obj):
        #return "%d" % obj
        return "{0:.0f}".format(obj)
