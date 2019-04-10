from formatter import Formatter

class TagsCount(Formatter):
    def format(self, string):
        if self.task['tags'] and len(self.task['tags']) > 0:
            return "[%d]" % len(self.task['tags'])
        else:
            return ''
