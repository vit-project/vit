from vit.formatter.start import Start

class StartAge(Start):
    def format_datetime(self, start, task):
        return self.age(start)
