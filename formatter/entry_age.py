from formatter.entry import Entry

class EntryAge(Entry):
    def format(self, dt):
        return self.age(dt)
