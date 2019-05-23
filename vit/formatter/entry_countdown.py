from vit.formatter.entry import Entry

class EntryCountdown(Entry):
    def format(self, entry, task):
        return self.countdown(entry)
