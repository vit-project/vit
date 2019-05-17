from vit.formatter.modified import Modified

class ModifiedCountdown(Modified):
    def format(self, modified, task):
        return self.countdown(modified)
