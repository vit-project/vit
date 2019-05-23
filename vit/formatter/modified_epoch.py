from vit.formatter.modified import Modified

class ModifiedEpoch(Modified):
    def format(self, modified, task):
        return self.epoch(modified)
