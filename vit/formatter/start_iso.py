from vit.formatter.start import Start

class StartIso(Start):
    def format_datetime(self, start, task):
        return self.iso(start)
