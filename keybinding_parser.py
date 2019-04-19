from future.utils import raise_
from functools import reduce

import re

BRACKETS_REGEX = re.compile("[<>]")

class KeybindingParser(object):
    def __init__(self):
        self.keybindings = {}
        self.multi_key_cache = {}

    def parse_keybinding_keys(self, keys):
        parsed_keys = ' '.join(re.sub(BRACKETS_REGEX, ' ', keys).strip().split()).lower()
        has_modifier = bool(re.match(BRACKETS_REGEX, keys))
        return parsed_keys, has_modifier

    def parse_keybinding_value(self, value, replacements={}):
        def reducer(accum, char):
            if char == '<':
                accum['in_brackets'] = True
                accum['bracket_string'] = ''
            elif char == '>':
                accum['in_brackets'] = False
                accum['key_command'].append(accum['bracket_string'].lower())
            elif char == '{':
                accum['in_variable'] = True
                accum['variable_string'] = ''
            elif char == '}':
                accum['in_variable'] = False
                if accum['variable_string'] in replacements:
                    accum['key_command'].append(replacements[accum['variable_string']])
                else:
                    raise_(ValueError, "unknown config variable '%s'" % accum['variable_string'])
            else:
                if accum['in_brackets']:
                    accum['bracket_string'] += char
                elif accum['in_variable']:
                    accum['variable_string'] += char
                else:
                    accum['key_command'].append(char)
            return accum
        accum = reduce(reducer, value, {'key_command': [], 'in_brackets': False, 'bracket_string': '', 'in_variable': False, 'variable_string': ''})
        return accum['key_command']

    def add_keybindings(self, bindings=[], replacements={}):
        for key_groups, value in bindings:
            for keys in key_groups.strip().split(','):
                parsed_keys, has_modifier = self.parse_keybinding_keys(keys)
                self.keybindings[parsed_keys] = {
                    'keys': self.parse_keybinding_value(value, replacements),
                    'has_modifier': has_modifier,
                }

    def build_multi_key_cache(self):
        alphabetic_key_combinations = []


