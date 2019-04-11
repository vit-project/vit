from formatter.tags import Tags

class TagsCount(Tags):
    def format(self, string):
        if self.task['tags'] and len(self.task['tags']) > 0:
            return "[%d]" % len(self.task['tags'])
        else:
            return ''
