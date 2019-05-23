from vit.formatter.modified import Modified

class ModifiedAge(Modified):
    def format(self, modified, task):
        return self.age(modified)
