from vit.formatter.modified import Modified

class ModifiedRemaining(Modified):
    def format(self, modified, task):
        return self.remaining(modified)
