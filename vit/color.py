import re
import urwid
from functools import cmp_to_key, wraps

from vit.color_mappings import task_256_to_urwid_256, task_bright_to_color

VALID_COLOR_MODIFIERS = [
    'bold',
    'underline',
]

class TaskColorConfig(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config, theme, theme_alt_backgrounds):
        self.config = config
        self.task_config = task_config
        self.theme = theme
        self.theme_alt_backgrounds = theme_alt_backgrounds
        self.include_subprojects = self.config.get('color', 'include_subprojects')
        self.task_256_to_urwid_256 = task_256_to_urwid_256()
        # NOTE: Because Taskwarrior disables color on piped commands, and I don't
        # see any portable way to get output from a system command in Python
        # without pipes, the 'color' config setting in Taskwarrior is not used, and
        # instead a custom setting is used.
        self.color_enabled = self.config.get('color', 'enabled')
        self.display_attrs_available, self.display_attrs = self.convert_color_config(self.task_config.filter_to_dict('^color\.'))
        self.project_display_attrs = self.get_project_display_attrs()
        if self.include_subprojects:
            self.add_project_children()
        self.inject_alt_background_display_attrs()

    def inject_alt_background_display_attrs(self):
        for display_attr in self.display_attrs.copy():
            name, display_attr_foreground_16, display_attr_background_16, _mono, display_attr_foreground_256, display_attr_background_256 = display_attr
            for modifier, alt_backgrounds in self.theme_alt_backgrounds.items():
                display_attr_modifier = name + modifier
                if self.has_display_attr(name):
                    self.display_attrs_available[display_attr_modifier] = True
                    alt_background_16, alt_background_256 = alt_backgrounds
                    new_background_16 = alt_background_16 if display_attr_background_16 == '' else display_attr_background_16
                    new_background_256 = alt_background_256 if display_attr_background_256 == '' else display_attr_background_256
                    self.display_attrs.append(self.make_display_attr(display_attr_modifier, display_attr_foreground_256, new_background_256, foreground_16=display_attr_foreground_16, background_16=new_background_16))
                else:
                    self.display_attrs_available[display_attr_modifier] = False

    def add_project_children(self):
        color_prefix = 'color.project.'
        for (display_attr, fg16, bg16, m, fg256, bg256) in self.project_display_attrs:
            for entry in self.task_config.projects:
                attr = '%s%s' % (color_prefix, entry)
                if not self.has_display_attr(attr) and attr.startswith('%s.' % display_attr):
                    self.display_attrs_available[attr] = True
                    self.display_attrs.append((attr, fg16, bg16, m, fg256, bg256))

    def has_display_attr(self, display_attr):
        return display_attr in self.display_attrs_available and self.display_attrs_available[display_attr]

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

    def make_display_attr(self, display_attr, foreground, background, foreground_16=None, background_16=None):
        # TODO: 256 colors need to be translated down to 16 color mode.
        foreground_16 = '' if foreground_16 is None else foreground_16
        background_16 = '' if background_16 is None else background_16
        return (display_attr, foreground_16, background_16, '', foreground, background)

    def has_color_config(self, foreground, background):
        return foreground != '' or background != ''

    def convert_colors(self, color_config):
        # TODO: Maybe a fancy regex eventually...
        color_config = task_bright_to_color(color_config).strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        foreground_parts, background_parts = self.make_color_parts(foreground, background)
        return self.convert_color_parts(foreground_parts), self.convert_color_parts(background_parts)

    def convert_color_parts(self, color_parts):
        sorted_parts = self.sort_color_parts(color_parts)
        remapped_colors = self.map_named_colors(sorted_parts)
        return ','.join(remapped_colors)

    def map_named_colors(self, color_parts):
        if len(color_parts) > 0 and color_parts[0] in self.task_256_to_urwid_256:
            color_parts[0] = self.task_256_to_urwid_256[color_parts[0]]
        return color_parts

    def make_color_parts(self, foreground, background):
        foreground_parts = self.split_color_parts(foreground)
        background_parts = self.split_color_parts(background)
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
    class Decorator(object):
        def color_enabled(func):
            @wraps(func)
            def verify_color_enabled(self, *args, **kwargs):
                return func(self, *args, **kwargs) if self.color_enabled else None
            return verify_color_enabled
    def __init__(self, color_config):
        self.color_config = color_config
        self.color_enabled = self.color_config.color_enabled
        self.theme_alt_backgrounds = self.color_config.theme_alt_backgrounds
        self.background_modifier = ''
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

    def set_background_modifier(self, modifier=''):
        self.background_modifier = modifier if modifier in self.theme_alt_backgrounds else ''

    def add_background_modifier(self, display_attr):
        return display_attr + self.background_modifier

    def make_display_attr(self, display_attr):
        return self.add_background_modifier(display_attr)

    def get_display_attr(self, display_attr):
        return self.make_display_attr(display_attr) if self.color_config.has_display_attr(display_attr) else None

    @Decorator.color_enabled
    def project_none(self):
        return self.get_display_attr('color.project.none')

    @Decorator.color_enabled
    def project(self, project):
        return self.get_display_attr('color.project.%s' % project)

    @Decorator.color_enabled
    def tag_none(self):
        return self.get_display_attr('color.tag.none')

    @Decorator.color_enabled
    def tag(self, tag):
        custom_value = 'color.tag.%s' % tag
        if self.color_config.has_display_attr(custom_value):
            return self.make_display_attr(custom_value)
        elif self.color_config.has_display_attr('color.tagged'):
            return self.make_display_attr('color.tagged')
        return None

    @Decorator.color_enabled
    def uda_none(self, name):
        return self.get_display_attr('color.uda.%s.none' % name)

    @Decorator.color_enabled
    def uda_common(self, name, value):
        custom_value = 'color.uda.%s' % name
        if self.color_config.has_display_attr(custom_value):
            return self.make_display_attr(custom_value)
        elif self.color_config.has_display_attr('color.uda'):
            return self.make_display_attr('color.uda')
        return None

    @Decorator.color_enabled
    def uda_string(self, name, value):
        if not value:
            return self.uda_none(name)
        else:
            custom_value = 'color.uda.%s.%s' % (name, value)
            if self.color_config.has_display_attr(custom_value):
                return self.make_display_attr(custom_value)
            return self.uda_common(name, value)

    @Decorator.color_enabled
    def uda_numeric(self, name, value):
        return self.uda_string(name, value)

    @Decorator.color_enabled
    def uda_duration(self, name, value):
        return self.uda_string(name, value)

    @Decorator.color_enabled
    def uda_date(self, name, value):
        # TODO: Maybe some special string indicators here?
        return self.uda_common(name, value) if value else self.uda_none(name)

    @Decorator.color_enabled
    def uda_indicator(self, name, value):
        return self.uda_string(name, value)

    @Decorator.color_enabled
    def keyword(self, text):
        return self.get_display_attr('color.keyword.%s' % text)

    @Decorator.color_enabled
    def blocking(self):
        return self.get_display_attr('color.blocking')

    @Decorator.color_enabled
    def due(self, state):
        return self.get_display_attr('color.%s' % state) if state else None

    @Decorator.color_enabled
    def status(self, status):
        if status == 'completed' or status == 'deleted':
            value = 'color.%s' % status
            if self.color_config.has_display_attr(value):
                return self.make_display_attr(value)
        return None

    @Decorator.color_enabled
    def blocked(self, depends):
        return self.get_display_attr('color.blocked')

    @Decorator.color_enabled
    def active(self, active):
        return self.get_display_attr('color.active') if active else None

    @Decorator.color_enabled
    def recurring(self, recur):
        return self.get_display_attr('color.recurring')

    @Decorator.color_enabled
    def scheduled(self, scheduled):
        return self.get_display_attr('color.scheduled') if scheduled else None

    @Decorator.color_enabled
    def until(self, until):
        return self.get_display_attr('color.until') if until else None
