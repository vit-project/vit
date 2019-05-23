from vit.formatter.due import Due

class DueIso(Due):
    def format_datetime(self, due, task):
        return self.iso(due)
