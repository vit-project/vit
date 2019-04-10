from formatter import String

class DescriptionCount(String):
    def format(self, string):
        if self.task['annotations']:
            return "%s [%d]" % (string, len(self.task['annotations']))
        else:
            return string
