import util
from formatter import Formatter

class Depends(Formatter):
    def format(self, depends, task):
        return ','.join(list(map(lambda t: str(util.task_id_or_uuid_short(t)), depends))) if depends else ''
