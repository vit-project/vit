import re
import urwid
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

from color_mappings import task_256_to_urwid_256, task_bright_to_color

VALID_COLOR_MODIFIERS = [
    'bold',
    'underline',
]

class TaskColorizer(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
        self.task_256_to_urwid_256 = task_256_to_urwid_256()
        self.color_enabled = self.task_config.subtree('color$', walk_subtree=False)['color'] == 'on'
        self.color_config = self.convert_color_config(self.task_config.filter_to_dict('^color\.'))
        self.color_precedence = self.task_config.subtree('rule.')['precedence']['color'].split(',')

    def convert_color_config(self, color_config):
        def convert(color):
            key, value = color
            foreground, background = self.convert_colors(value)
            # TODO: Maybe translate down to basic 16 foreground/background as
            # well?
            return (key, '', '', '', foreground, background)
        return list(map(convert, color_config.items()))

    def convert_colors(self, color_config):
        # TODO: Maybe a fancy regex eventually...
        color_config = task_bright_to_color(color_config).strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        foreground_parts, background_parts = self.check_invert_color_parts(foreground, background)
        return self.convert(foreground_parts), self.convert(background_parts)

    def convert(self, color_parts):
        sorted_parts = self.sort_color_parts(color_parts)
        remapped_colors = self.map_named_colors(sorted_parts)
        return ','.join(remapped_colors)

    def map_named_colors(self, color_parts):
        if len(color_parts) > 0 and color_parts[0] in self.task_256_to_urwid_256:
            color_parts[0] = self.task_256_to_urwid_256[color_parts[0]]
        return color_parts

    def check_invert_color_parts(self, foreground, background):
        foreground_parts = self.split_color_parts(foreground)
        background_parts = self.split_color_parts(background)
        inverse = False
        if 'inverse' in foreground_parts:
            foreground_parts.remove('inverse')
            inverse = True
        if 'inverse' in background_parts:
            background_parts.remove('inverse')
            inverse = True
        if inverse:
            return background_parts, foreground_parts
        else:
            return foreground_parts, background_parts

    def split_color_parts(self, color_parts):
        parts = color_parts.split() if color_parts else []
        return parts

    def is_modifier(self, elem):
        return elem in VALID_COLOR_MODIFIERS

    def sort_color_parts(self, color_parts):
        def comparator(first, second):
            if self.is_modifier(first) and not self.is_modifier(second):
                return 1
            elif not self.is_modifier(first) and self.is_modifier(second):
                return -1
            else:
                return 0
        return sorted(color_parts, key=cmp_to_key(comparator))
