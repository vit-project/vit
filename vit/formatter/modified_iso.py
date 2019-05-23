from vit.formatter.modified import Modified

class ModifiedIso(Modified):
    def format(self, modified, task):
        return self.iso(modified)
