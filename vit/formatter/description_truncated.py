from vit.formatter.description import Description

class DescriptionTruncated(Description):
    def format(self, description, task):
        if not description:
            return self.empty()
        truncated_description = self.format_description_truncated(description)
        width = len(truncated_description)
        colorized_description = self.colorize_description(truncated_description)
        return (width, colorized_description)
