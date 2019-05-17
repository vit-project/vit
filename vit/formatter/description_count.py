from vit.formatter.description import Description

class DescriptionCount(Description):
    def format(self, description, task):
        if not description:
            return self.empty()
        width = len(description)
        colorized_description = self.colorize_description(description)
        if not task['annotations']:
            return (width, colorized_description)
        else:
            count_width, colorized_description = self.format_count(colorized_description, task)
            return (width + count_width, colorized_description)

    def format_count(self, colorized_description, task):
        count_string = self.format_annotation_count(task)
        return len(count_string), colorized_description + [(None, count_string)]

    def format_annotation_count(self, task):
        return " [%d]" % len(task['annotations'])
