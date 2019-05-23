from vit.formatter.entry import Entry

class EntryEpoch(Entry):
    def format(self, entry, task):
        return self.epoch(entry)
