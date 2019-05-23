from vit.formatter.entry import Entry

class EntryRemaining(Entry):
    def format(self, entry, task):
        return self.remaining(entry)
