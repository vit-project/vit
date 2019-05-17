from vit.formatter import String

class Status(String):
    def markup_element(self, status):
        return (self.colorize(status), self.status_format(status))

    def colorize(self, status):
        return self.colorizer.status(status)

    def status_format(self, status):
        return status.capitalize()
