from vit.formatter.description import Description

class DescriptionDesc(Description):
    def format(self, description, task):
        if not description:
            return self.empty()
        colorized_description = self.colorize_description(description)
        return (len(description), colorized_description)
