from functools import reduce

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os
import re

from vit import util

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
BRACKETS_REGEX = re.compile("[<>]")
DEFAULT_KEYBINDINGS_SECTIONS = ('global', 'navigation', 'command', 'report')
CONFIG_NAME_SPECIAL_KEY_SUBSTITUTIONS = {
    'colon': ':',
    'equals': '=',
    'space': ' ',
}

class KeybindingError(Exception):
    pass

class KeybindingParser(object):
    def __init__(self, loader, config, action_registry):
        self.loader = loader
        self.config = config
        self.action_registry = action_registry
        self.actions = self.action_registry.get_actions()
        self.noop_action_name = self.action_registry.make_action_name(self.action_registry.noop_action_name)
        self.default_keybinding_name = self.config.get('vit', 'default_keybindings')
        self.default_keybindings = configparser.SafeConfigParser()
        self.default_keybindings.optionxform=str
        self.sections = DEFAULT_KEYBINDINGS_SECTIONS
        self.keybindings = {}
        self.multi_key_cache = {}

    def is_keybinding(self, keys):
        return keys in self.keybindings

    def items(self, section):
        try:
            return self.default_keybindings.items(section)
        except configparser.NoSectionError:
            return []

    def load_default_keybindings(self):
        name = self.default_keybinding_name
        template = '%s/keybinding/%s.ini'
        user_keybinding_file = template % (self.loader.user_config_dir, name)
        keybinding_file = template % (BASE_DIR, name)
        if util.file_readable(user_keybinding_file):
            self.default_keybindings.read(user_keybinding_file)
        elif util.file_readable(keybinding_file):
            self.default_keybindings.read(keybinding_file)
        else:
            raise KeybindingError("default_keybindings setting '%s' invalid, file not found" % name)
        for section in self.sections:
            bindings = self.items(section)
            self.add_keybindings(bindings)

    def keybinding_special_keys_substitutions(self, name):
        if name in CONFIG_NAME_SPECIAL_KEY_SUBSTITUTIONS:
            name = CONFIG_NAME_SPECIAL_KEY_SUBSTITUTIONS[name]
        return name

    def parse_keybinding_keys(self, keys):
        has_modifier = bool(re.match(BRACKETS_REGEX, keys))
        parsed_keys = ' '.join(re.sub(BRACKETS_REGEX, ' ', keys).strip().split()).lower() if has_modifier else keys
        return self.keybinding_special_keys_substitutions(parsed_keys), has_modifier

    def parse_keybinding_value(self, value, replacements={}):
        def reducer(accum, char):
            if char == '<':
                accum['in_brackets'] = True
                accum['bracket_string'] = ''
            elif char == '>':
                accum['in_brackets'] = False
                accum['keybinding'].append(accum['bracket_string'].lower())
            elif char == '{':
                accum['in_variable'] = True
                accum['variable_string'] = ''
            elif char == '}':
                accum['in_variable'] = False
                if accum['variable_string'] in self.actions:
                    accum['action_name'] = accum['variable_string']
                elif accum['variable_string'] in replacements:
                    accum['keybinding'].append(replacements[accum['variable_string']])
                else:
                    raise ValueError("unknown config variable '%s'" % accum['variable_string'])
            else:
                if accum['in_brackets']:
                    accum['bracket_string'] += char
                elif accum['in_variable']:
                    accum['variable_string'] += char
                else:
                    accum['keybinding'].append(char)
            return accum
        accum = reduce(reducer, value, {
            'keybinding': [],
            'action_name': None,
            'in_brackets': False,
            'bracket_string': '',
            'in_variable': False,
            'variable_string': '',
        })
        return accum['keybinding'], accum['action_name']

    def validate_parsed_value(self, key_groups, bound_keys, action_name):
        if bound_keys and action_name:
            raise KeybindingError("keybindings '%s' unsupported configuration: ACTION_ variables must be used alone." % key_groups)

    def is_noop_action(self, keybinding):
        return True if 'action_name' in keybinding and keybinding['action_name'] == self.noop_action_name else False

    def filter_noop_actions(self, keybindings):
        return {keys:value for (keys, value) in keybindings.items() if not self.is_noop_action(keybindings[keys])}

    def get_keybindings(self):
        return self.keybindings

    def add_keybindings(self, bindings=[], replacements={}):
        for key_groups, value in bindings:
            bound_keys, action_name = self.parse_keybinding_value(value, replacements)
            self.validate_parsed_value(key_groups, bound_keys, action_name)
            for keys in key_groups.strip().split(','):
                parsed_keys, has_modifier = self.parse_keybinding_keys(keys)
                self.keybindings[parsed_keys] = {
                    'label': keys,
                    'has_modifier': has_modifier,
                }
                if action_name:
                    self.keybindings[parsed_keys]['action_name'] = action_name
                else:
                    self.keybindings[parsed_keys]['keys'] = bound_keys
        self.keybindings = self.filter_noop_actions(self.keybindings)
        return self.get_keybindings()

