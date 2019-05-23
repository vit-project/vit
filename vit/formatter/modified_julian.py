from vit.formatter.modified import Modified

class ModifiedJulian(Modified):
    def format(self, modified, task):
        return self.julian(modified)
