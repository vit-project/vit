from vit.formatter.start import Start

class StartRemaining(Start):
    def format_datetime(self, start, task):
        return self.remaining(start)
