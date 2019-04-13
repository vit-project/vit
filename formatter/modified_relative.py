from formatter.modified import Modified

class ModifiedRelative(Modified):
    def format(self, modified, task):
        return self.relative(modified)
