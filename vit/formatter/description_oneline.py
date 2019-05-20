from vit.formatter.description import Description

class DescriptionOneline(Description):
    def format_combined(self, colorized_description, task):
        formatted_annotations = self.format_annotations(task)
        return 0, colorized_description + [(None, formatted_annotations)]

    def format_annotations(self, task):
        formatted_annotations = [self.format_annotation(annotation) for annotation in task['annotations']]
        return "".join(formatted_annotations)

    def format_annotation(self, annotation):
        return ' %s %s' % (annotation['entry'].strftime(self.formatter.annotation), annotation['description'])
