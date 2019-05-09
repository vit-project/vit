from formatter.start import Start

class StartRelative(Start):
    def format_datetime(self, start):
        return self.relative(start)
