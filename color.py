import re
import urwid
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

from color_mappings import task_256_to_urwid_256, task_bright_to_color

VALID_COLOR_MODIFIERS = [
    'bold',
    'underline',
]

class TaskColorConfig(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
        self.include_subprojects = self.config.get('color', 'include_subprojects')
        self.task_256_to_urwid_256 = task_256_to_urwid_256()
        self.color_enabled = self.task_config.subtree('color$', walk_subtree=False)['color'] == 'on'
        self.display_attrs_available, self.display_attrs = self.convert_color_config(self.task_config.filter_to_dict('^color\.'))
        self.project_display_attrs = self.get_project_display_attrs()
        self.color_precedence = self.task_config.subtree('rule.')['precedence']['color'].split(',')
        if self.include_subprojects:
            self.add_project_children()

    def add_project_children(self):
        color_prefix = 'color.project.'
        for (display_attr, fg16, bg16, m, fg256, bg256) in self.project_display_attrs:
            for entry in self.task_config.projects:
                attr = '%s%s' % (color_prefix, entry)
                if not self.has_display_attr(attr) and attr.startswith('%s.' % display_attr):
                    self.display_attrs_available[attr] = True
                    self.display_attrs.append((attr, fg16, bg16, m, fg256, bg256))

    def has_display_attr(self, display_attr):
        # TODO: There are only a few attributes that need to have their names
        # transformed by task_config.transform_string_leaves() -- would it be
        # better just to hard code them in the colorizer, or use this function
        # against all display attrs? Concerned about the overhead...
        display_attr = self.task_config.transform_string_leaves(display_attr)
        return display_attr in self.display_attrs_available and self.display_attrs_available[display_attr]

    # TODO: There are only a few attributes that need to have their names
    # transformed by task_config.transform_string_leaves() -- would it be
    # better just to hard code them in the colorizer, or use this function
    # against all display attrs? Concerned about the overhead...
    def display_attr(self, display_attr):
        return self.task_config.transform_string_leaves(display_attr)

    def get_project_display_attrs(self):
        return sorted([(a, fg16, bg16, m, fg256, bg256) for (a, fg16, bg16, m, fg256, bg256) in self.display_attrs if self.display_attrs_available[a] and self.is_project_display_attr(a)], reverse=True)

    def is_project_display_attr(self, display_attr):
        return display_attr[0:14] == 'color.project.'

    def convert_color_config(self, color_config):
        display_attrs_available = {}
        display_attrs = []
        for key, value in color_config.items():
            foreground, background = self.convert_colors(value)
            available = self.has_color_config(foreground, background)
            display_attrs_available[key] = available
            if available:
                display_attrs.append(self.make_display_attr(key, foreground, background))
        return display_attrs_available, display_attrs

    def make_display_attr(self, display_attr, foreground, background):
        # TODO: Non-standard colors need to be translated down to standard.
        # TODO: Why aren't 256 colors being used when no basic colors are
        # provided?
        return (display_attr, foreground, background, '', foreground, background)

    def has_color_config(self, foreground, background):
        return foreground != '' or background != ''

    def convert_colors(self, color_config):
        # TODO: Maybe a fancy regex eventually...
        color_config = task_bright_to_color(color_config).strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        foreground_parts, background_parts = self.check_invert_color_parts(foreground, background)
        return self.convert(foreground_parts), self.convert(background_parts)

    # TODO: Better method name please...
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

class TaskColorizer(object):
    def __init__(self, color_config):
        self.color_config = color_config
        self.init_keywords()

    def init_keywords(self):
        try:
            self.keywords = self.color_config.task_config.subtree('color.')['keyword']
            self.any_keywords_regex = re.compile('(%s)' % '|'.join(self.keywords.keys()))
        except KeyError:
            self.keywords = []
            self.any_keywords_regex = None

    def has_keywords(self, text):
        return self.any_keywords_regex and self.any_keywords_regex.search(text)

    def extract_keyword_parts(self, text):
        if self.has_keywords(text):
            parts = self.any_keywords_regex.split(text)
            first_part = parts.pop(0)
            return first_part, parts
        return None, None

    def project_none(self):
        if self.color_config.has_display_attr('color.project.none'):
            return 'color.project.none'
        return None

    def project(self, project):
        display_attr = 'color.project.%s' % project
        return display_attr if self.color_config.has_display_attr(display_attr) else None

    def tag_none(self):
        if self.color_config.has_display_attr('color.tag.none'):
            return 'color.tag.none'
        return None

    def tag(self, tag):
        custom = 'color.tag.%s' % tag
        if self.color_config.has_display_attr(custom):
            return custom
        elif self.color_config.has_display_attr('color.tagged'):
            return 'color.tagged'
        return None

    def uda_none(self, name):
        none_value = 'color.uda.%s.none' % name
        if self.color_config.has_display_attr(none_value):
            return none_value
        return None

    def uda_common(self, name, value):
        custom = 'color.uda.%s' % name
        if self.color_config.has_display_attr(custom):
            return custom
        elif self.color_config.has_display_attr('color.uda'):
            return 'color.uda'
        return None

    def uda_string(self, name, value):
        if not value:
            return self.uda_none(name)
        else:
            custom_value = 'color.uda.%s.%s' % (name, value)
            if self.color_config.has_display_attr(custom_value):
                return custom_value
            return self.uda_common(name, value)

    def uda_numeric(self, name, value):
        return self.uda_string(name, value)

    def uda_duration(self, name, value):
        return self.uda_string(name, value)

    def uda_date(self, name, value):
        if not value:
            return self.uda_none(name)
        else:
            # TODO: Maybe some special string indicators here?
            return self.uda_common(name, value)

    def keyword(self, text):
        # TODO: Any way to optimize storing this display attr name?
        value = 'color.keyword.%s' % text
        return None if not self.color_config.has_display_attr(value) else value

    def blocking(self):
        if self.color_config.has_display_attr('color.blocking'):
            return 'color.blocking'
        return None

    def due(self, state):
        if state:
            value = 'color.%s' % state
            if self.color_config.has_display_attr(value):
                return self.color_config.display_attr(value)
        return None
