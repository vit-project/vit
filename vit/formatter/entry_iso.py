from vit.formatter.entry import Entry

class EntryIso(Entry):
    def format(self, entry, task):
        return self.iso(entry)
