from formatter import String

class Description(String):
    def format(self, description, task):
        if task['annotations']:
            return self.format_combined(description, task)
        else:
            return description

    def format_combined(self, description, task):
        return '%s\n%s' % (description, self.format_annotations(task))

    def format_annotations(self, task):
        return "\n".join([self.format_annotation(a) for a in task['annotations']])

    def format_annotation(self, annotation):
        return '  %s %s' % (annotation['entry'].strftime(self.defaults.annotation), annotation['description'])
