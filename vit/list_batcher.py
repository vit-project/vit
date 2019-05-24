DEFAULT_BATCH_SIZE=100

class ListBatchError(Exception):
    pass

class ListBatcher(object):
    def __init__(self, batch_from, batch_to, batch_to_formatter=None, default_batch_size=DEFAULT_BATCH_SIZE):
        self.batch_from = batch_from
        self.batch_to = batch_to
        self.batch_to_formatter = batch_to_formatter
        self.default_batch_size = default_batch_size
        self.last_position = 0
        self.batching_complete = False

    def add(self, batch_size=None):
        if self.batching_complete:
            return True
        batch_size = self.get_batch_size(batch_size)
        self.load_batch(batch_size)
        if self.is_batching_complete():
            self.batching_complete = True
        return self.batching_complete

    def get_last_position(self):
        return self.last_position

    def load_batch(self, batch_size):
        new_position = self.last_position + batch_size
        partial = self.batch_from[self.last_position:new_position]
        if self.batch_to_formatter:
            partial = self.batch_to_formatter(partial, self.last_position)
        self.batch_to += partial
        self.last_position = new_position

    def is_batching_complete(self):
        return self.last_position >= len(self.batch_from)

    def batch_remainder(self):
        return len(self.batch_from) - self.last_position

    def get_batch_size(self, batch_size):
        remainder = self.batch_remainder()
        if batch_size == 0:
            return remainder
        else:
            if batch_size is None:
                batch_size = self.default_batch_size
            return remainder if batch_size > remainder else batch_size
