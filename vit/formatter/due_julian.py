from vit.formatter.due import Due

class DueJulian(Due):
    def format_datetime(self, due, task):
        return self.julian(due)
