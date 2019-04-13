from formatter.entry import Entry

class EntryAge(Entry):
    def format(self, entry, task):
        return self.age(entry)
