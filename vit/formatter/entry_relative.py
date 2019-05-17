from vit.formatter.entry import Entry

class EntryRelative(Entry):
    def format(self, entry, task):
        return self.relative(entry)
