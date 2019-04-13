from formatter.tags import Tags

class TagsCount(Tags):
    def format(self, tags, task):
        if tags and len(tags) > 0:
            return "[%d]" % len(tags)
        else:
            return ''
