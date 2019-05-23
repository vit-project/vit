from vit.formatter.start import Start

class StartJulian(Start):
    def format_datetime(self, start, task):
        return self.julian(start)
