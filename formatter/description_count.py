from formatter.description import Description

class DescriptionCount(Description):
    def format(self, string):
        if self.task['annotations']:
            return "%s [%d]" % (string or '', len(self.task['annotations']))
        else:
            return string
