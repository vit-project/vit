from vit.formatter import String

class Parent(String):
    def format(self, parent, task):
        return parent['uuid'] if parent else ''
