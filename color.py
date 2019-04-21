import re
import urwid

COLOR_SUB_REGEX = re.compile('^color(\d\d?\d?)$')
RGB_SUB_REGEX = re.compile('^rgb(\d\d\d)$')
GRAY_SUB_REGEX = re.compile('^gray(\d\d?)$')

class TaskColorizer(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
        self.color_enabled = self.task_config.subtree('color$', walk_subtree=False)['color'] == 'on'
        self.color_config = self.convert_color_config(self.task_config.subtree('color.'))
        self.color_precedence = self.task_config.subtree('rule.')['precedence']['color'].split(',')

    def convert_color_config(self, elem):
        if isinstance(elem, dict):
            return {key: self.convert_color_config(value) for key, value in elem.items()}
        else:
            return self.convert_colors(elem)

    def convert_colors(self, color_config):
        # TODO: Maybe a fancy regex eventually...
        color_config = color_config.strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        return {
            'foreground': self.convert_color_parts(foreground),
            'background': self.convert_color_parts(background),
        }

    def convert_color_parts(self, color_parts):
        return list(map(lambda p: self.convert_color(p), color_parts.split())) if color_parts else []

    def convert_color(self, color):
        return COLOR_SUB_REGEX.sub(r'h\1', RGB_SUB_REGEX.sub(r'#\1', GRAY_SUB_REGEX.sub(r'g\1', color)))
