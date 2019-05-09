from formatter.start import Start

class StartActive(Start):
    def format_datetime(self, start, task):
        return '*' if self.get_active_state(start, task) else ''
