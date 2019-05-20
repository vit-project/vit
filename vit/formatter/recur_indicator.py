from vit.formatter.recur import Recur

class RecurIndicator(Recur):
    def format_duration(self, recur):
        return '' if not recur else self.formatter.indicator_recurrence
