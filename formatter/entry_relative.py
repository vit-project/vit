from formatter.entry import Entry

class EntryRelative(Entry):
    def format(self, dt):
        return self.relative(dt)
