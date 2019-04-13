from formatter.description import Description

class DescriptionCount(Description):
    def format(self, description, task):
        if task['annotations']:
            return "%s [%d]" % (description or '', len(task['annotations']))
        else:
            return description
