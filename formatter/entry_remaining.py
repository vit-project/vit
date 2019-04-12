from formatter.entry import Entry

class EntryRemaining(Entry):
    def format(self, dt):
        return self.remaining(dt)
