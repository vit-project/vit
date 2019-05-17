from vit.formatter.tags import Tags

class TagsCount(Tags):
    def format(self, tags, task):
        if not tags:
            return self.markup_none(self.colorizer.tag_none())
        elif len(tags) == 1:
            return (3, (self.colorizer.tag(list(tags)[0]), '[1]'))
        else:
            tag_length = len(tags)
            indicator = '[%d]' % tag_length
            return (tag_length + 2, (self.colorizer.tag(''), indicator))
