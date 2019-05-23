from vit.formatter.due import Due

class DueEpoch(Due):
    def format_datetime(self, due, task):
        return self.epoch(due)
