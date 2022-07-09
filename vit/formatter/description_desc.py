from vit.formatter.description import Description
from vit.util import unicode_len

class DescriptionDesc(Description):
    def format(self, description, task):
        if not description:
            return self.empty()
        colorized_description = self.colorize_description(description)
        return (unicode_len(description), colorized_description)
