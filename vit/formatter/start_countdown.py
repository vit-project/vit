from vit.formatter.start import Start

class StartCountdown(Start):
    def format_datetime(self, start, task):
        return self.countdown(start)
