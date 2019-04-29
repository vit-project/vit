from formatter import Marker

class Markers(Marker):
    def format(self, _, task):
        text_markup = []
        width = 0
        if self.mark_tags and task['tags']:
            width, text_markup = self.format_tags(width, text_markup, task['tags'])
        if self.mark_project and task['project']:
            width, text_markup = self.format_project(width, text_markup, task['project'])
        return (width, '' if width == 0 else text_markup)

    def format_tags(self, width, text_markup, tags):
        if (len(tags) == 1):
            tag = list(tags)[0]
            custom_label = 'tag.%s.label' % tag
            label = self.labels['tag.label'] if not custom_label in self.labels else self.labels[custom_label]
            width += len(label)
            text_markup += [(self.colorizer.tag(tag), label)]
            return width, text_markup
        else:
            label = self.labels['tag.label']
            width += len(label)
            text_markup += [(self.colorizer.tag(''), label)]
            return width, text_markup

    def format_project(self, width, text_markup, project):
        custom_label = 'project.%s.label' % project
        label = self.labels['project.label'] if not custom_label in self.labels else self.labels[custom_label]
        width += len(label)
        text_markup += [(self.colorizer.project(project), label)]
        return width, text_markup
