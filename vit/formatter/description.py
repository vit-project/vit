from functools import reduce

from vit.formatter import String

class Description(String):
    def format(self, description, task):
        if not description:
            return self.empty()
        width = len(description)
        colorized_description = self.colorize_description(description)
        if task['annotations']:
            annotation_width, colorized_description = self.format_combined(colorized_description, task)
            if annotation_width > width:
                width = annotation_width
        return (width, colorized_description)

    def format_description_truncated(self, description):
        return '%s...' % description[:self.formatter.description_truncate_len] if len(description) > self.formatter.description_truncate_len else description

    def format_combined(self, colorized_description, task):
        annotation_width, formatted_annotations = self.format_annotations(task)
        return annotation_width, colorized_description + [(None, "\n"), (None, formatted_annotations)]

    def format_annotations(self, task):
        def reducer(accum, annotation):
            width, formatted_list = accum
            formatted = self.format_annotation(annotation)
            new_width = len(formatted)
            if new_width > width:
                width = new_width
            formatted_list.append(formatted)
            return (width, formatted_list)
        width, formatted_annotations = reduce(reducer, task['annotations'], (0, []))
        return width, "\n".join(formatted_annotations)

    def format_annotation(self, annotation):
        return '  %s %s' % (annotation['entry'].strftime(self.formatter.annotation), annotation['description'])

    def colorize(self, part):
        return self.colorizer.keyword(part)

    def colorize_description(self, description):
        first_part, rest = self.colorizer.extract_keyword_parts(description)
        if first_part is None:
            return [(None, description)]
        def reducer(accum, part):
            if part:
                last_color, last_part = accum[-1]
                color, part = self.markup_element(part)
                if color == last_color:
                    accum[-1] = (last_color, last_part + part)
                    return accum
                else:
                    return accum + [(color, part)]
            return accum
        return reduce(reducer, rest, [self.markup_element(first_part)])
