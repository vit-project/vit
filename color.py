import re
import urwid
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

COLOR_SUB_REGEX = re.compile('^color(\d\d?\d?)$')
RGB_SUB_REGEX = re.compile('^rgb(\d\d\d)$')
GRAY_SUB_REGEX = re.compile('^gray(\d\d?)$')
FOREGROUND_NAMED_COLOR_MAP = {
    'red': 'dark red',
    'green': 'dark green',
    'blue': 'dark blue',
    'cyan': 'dark cyan',
    'magenta': 'dark magenta',
    'gray': 'light gray',
}
BACKGROUND_NAMED_COLOR_MAP = {
    'red': 'light red',
    'green': 'light green',
    'blue': 'light blue',
    'cyan': 'light cyan',
    'magenta': 'light magenta',
    'gray': 'dark gray',
}
VALID_COLOR_MODIFIERS = [
    'bold',
    'underline',
    # TODO: How to translate this?
    #'inverse',
]

class TaskColorizer(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
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
        color_config = color_config.strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        return self.convert_foreground(foreground), self.convert_background(background)

    def convert_foreground(self, foreground):
        return ','.join(self.map_named_foreground_colors(self.sort_color_parts(self.convert_color_parts(foreground))))

    def convert_background(self, background):
        return ','.join(self.map_named_background_colors(self.sort_color_parts(self.convert_color_parts(background))))

    def convert_color_parts(self, color_parts):
        parts = list(map(lambda p: self.convert_color(p), color_parts.split())) if color_parts else []
        if 'bright' in parts:
            parts.remove('bright')
        return parts

    def convert_color(self, color):
        return COLOR_SUB_REGEX.sub(r'h\1', RGB_SUB_REGEX.sub(r'#\1', GRAY_SUB_REGEX.sub(r'g\1', color)))

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

    def map_named_foreground_colors(self, color_parts):
        if len(color_parts) > 0 and color_parts[0] in FOREGROUND_NAMED_COLOR_MAP:
            color_parts[0] = FOREGROUND_NAMED_COLOR_MAP[color_parts[0]]
        return color_parts

    def map_named_background_colors(self, color_parts):
        if len(color_parts) > 0 and color_parts[0] in BACKGROUND_NAMED_COLOR_MAP:
            color_parts[0] = BACKGROUND_NAMED_COLOR_MAP[color_parts[0]]
        return color_parts
