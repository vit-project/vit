from formatter.entry import Entry

class EntryCountdown(Entry):
    def format(self, dt):
        return self.countdown(dt)
