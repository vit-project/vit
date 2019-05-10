from formatter.entry import Entry

class EntryJulian(Entry):
    def format(self, entry, task):
        return self.julian(entry)
