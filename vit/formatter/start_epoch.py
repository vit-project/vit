from vit.formatter.start import Start

class StartEpoch(Start):
    def format_datetime(self, start, task):
        return self.epoch(start)
