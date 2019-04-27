from formatter import List

class Tags(List):
    def format(self, tags, task):
        if not tags:
            return (0, '')
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

    def color(self, tag):
        custom = 'color.tag.%s' % tag
        if self.has_display_attr(custom):
            return custom
        elif self.has_display_attr('color.tagged'):
            return 'color.tagged'
        return None
