import unittest

from vit.color_mappings import task_256_to_urwid_256


class TestColorMappings(unittest.TestCase):

    def test_maps_gray_and_grey_base_name(self):
        mapping = task_256_to_urwid_256()
        self.assertEqual(mapping['gray'], 'light gray')
        self.assertEqual(mapping['grey'], 'light gray')

    def test_maps_grey_scale_variants(self):
        mapping = task_256_to_urwid_256()
        self.assertEqual(mapping['gray10'], mapping['grey10'])
        self.assertEqual(mapping['grey10'], 'g40')


if __name__ == '__main__':
    unittest.main()
