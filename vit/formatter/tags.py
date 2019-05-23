from vit.formatter import Formatter

class Tags(Formatter):
    def format(self, tags, task):
        if not tags:
            return self.markup_none(self.colorizer.tag_none())
        elif len(tags) == 1:
            tag = list(tags)[0]
            return (len(tag), self.markup_element(tag))
        else:
            last_tag = list(tags)[-1]
            width = 0
            text_markup = []
            for tag in tags:
                width += len(tag)
                text_markup += [self.markup_element(tag)]
                if tag != last_tag:
                    width += 1
                    text_markup += [',']
            return (width, text_markup)

    def colorize(self, tag):
        return self.colorizer.tag(tag)
