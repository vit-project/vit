from vit import util
from vit.formatter.parent import Parent

class ParentShort(Parent):
    def format(self, parent, task):
        return util.uuid_short(parent['uuid']) if parent else ''
