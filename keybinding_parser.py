from future.utils import raise_
from functools import reduce

import re

BRACKETS_REGEX = re.compile("[<>]")

class KeybindingParser(object):
    def __init__(self):
        self.keybindings = {}

    def parse_keybinding_key(self, key):
        return ' '.join(re.sub(BRACKETS_REGEX, ' ', key).strip().split()).lower()

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
        for keys, value in bindings:
            for key in keys.strip().split(','):
                self.keybindings[self.parse_keybinding_key(key)] = self.parse_keybinding_value(value, replacements)


