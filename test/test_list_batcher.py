import unittest

from pprint import pprint
from vit.list_batcher import ListBatcher

DEFAULT_BATCH_FROM = list('abcdefghijklmnopqrstuvwxyz')

def default_batcher():
    batch_to = []
    return ListBatcher(DEFAULT_BATCH_FROM, batch_to), batch_to

class TestListBatcher(unittest.TestCase):

    def test_batch_default_batch(self):
      batcher, batch_to = default_batcher()
      complete = batcher.add()
      self.assertEqual(complete, True)
      self.assertEqual(batcher.get_last_position(), len(DEFAULT_BATCH_FROM))
      self.assertEqual(batch_to, DEFAULT_BATCH_FROM)

    def test_batch_1(self):
      batcher, batch_to = default_batcher()
      complete = batcher.add(1)
      self.assertEqual(complete, False)
      self.assertEqual(batcher.get_last_position(), 1)
      self.assertEqual(batch_to, ['a'])

    def test_batch_5(self):
      batcher, batch_to = default_batcher()
      complete = batcher.add(5)
      self.assertEqual(complete, False)
      self.assertEqual(batcher.get_last_position(), 5)
      self.assertEqual(batch_to, ['a', 'b', 'c', 'd', 'e'])

    def test_batch_1_and_1(self):
      batcher, batch_to = default_batcher()
      batcher.add(1)
      complete = batcher.add(1)
      self.assertEqual(complete, False)
      self.assertEqual(batcher.get_last_position(), 2)
      self.assertEqual(batch_to, ['a', 'b'])

    def test_batch_1_and_rest(self):
      batcher, batch_to = default_batcher()
      batcher.add(1)
      complete = batcher.add(0)
      self.assertEqual(complete, True)
      self.assertEqual(batcher.get_last_position(), len(DEFAULT_BATCH_FROM))
      self.assertEqual(batch_to, DEFAULT_BATCH_FROM)

    def test_batch_batch_size_greater_than_default(self):
      batcher, batch_to = default_batcher()
      complete = batcher.add(100000)
      self.assertEqual(complete, True)
      self.assertEqual(batcher.get_last_position(), len(DEFAULT_BATCH_FROM))
      self.assertEqual(batch_to, DEFAULT_BATCH_FROM)

    def test_batch_add_on_completed(self):
      batcher, batch_to = default_batcher()
      complete = batcher.add()
      self.assertEqual(complete, True)
      complete = batcher.add()
      self.assertEqual(complete, True)
      self.assertEqual(batcher.get_last_position(), len(DEFAULT_BATCH_FROM))
      self.assertEqual(batch_to, DEFAULT_BATCH_FROM)

    def test_batch_5_with_formatter(self):
      def formatter(partial, start_idx):
          return ['before'] + [row * 2 for row in partial] + ['after']
      batch_to = []
      batcher = ListBatcher(DEFAULT_BATCH_FROM, batch_to, batch_to_formatter=formatter)
      complete = batcher.add(5)
      self.assertEqual(complete, False)
      self.assertEqual(batcher.get_last_position(), 5)
      self.assertEqual(batch_to, ['before', 'aa', 'bb', 'cc', 'dd', 'ee', 'after'])

if __name__ == '__main__':
    unittest.main()
