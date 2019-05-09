from formatter.start import Start

class StartRelative(Start):
    def format_datetime(self, start, task):
        return self.relative(start)
