import util
from formatter.uuid import Uuid

class UuidShort(Uuid):
    def format(self, obj):
        return util.uuid_short(obj)
