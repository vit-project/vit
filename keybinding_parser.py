from future.utils import raise_
from functools import reduce

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os
import re

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
BRACKETS_REGEX = re.compile("[<>]")

class KeybindingError(Exception):
    pass

class KeybindingParser(object):
    def __init__(self, config, actions):
        self.config = config
        self.actions = actions
        self.keybindings = {}
        self.multi_key_cache = {}
        self.load_default_keybindings()

    def load_default_keybindings(self):
        self.default_keybindings = configparser.SafeConfigParser()
        self.default_keybindings.optionxform=str
        self.default_keybindings.read('%s/keybinding/%s.ini' % (FILE_DIR, self.config.get('vit', 'default_keybindings')))
        bindings = self.default_keybindings.items('keybinding')
        self.add_keybindings(bindings)

    def parse_keybinding_keys(self, keys):
        has_modifier = bool(re.match(BRACKETS_REGEX, keys))
        parsed_keys = ' '.join(re.sub(BRACKETS_REGEX, ' ', keys).strip().split()).lower() if has_modifier else keys
        return parsed_keys, has_modifier

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
                    # TODO: Some way to enforce errors if anything besides an
                    # action is declared.
                    accum['keybinding'] = self.actions[accum['variable_string']]['callback']
                elif accum['variable_string'] in replacements:
                    accum['keybinding'].append(replacements[accum['variable_string']])
                else:
                    raise_(ValueError, "unknown config variable '%s'" % accum['variable_string'])
            else:
                if accum['in_brackets']:
                    accum['bracket_string'] += char
                elif accum['in_variable']:
                    accum['variable_string'] += char
                else:
                    accum['keybinding'].append(char)
            return accum
        accum = reduce(reducer, value, {'keybinding': [], 'in_brackets': False, 'bracket_string': '', 'in_variable': False, 'variable_string': ''})
        return accum['keybinding']

    def add_keybindings(self, bindings=[], replacements={}):
        for key_groups, value in bindings:
            for keys in key_groups.strip().split(','):
                parsed_keys, has_modifier = self.parse_keybinding_keys(keys)
                self.keybindings[parsed_keys] = {
                    # TODO: Actions should probably have their own dict key.
                    'keys': self.parse_keybinding_value(value, replacements),
                    'has_modifier': has_modifier,
                }

    def sort_keybindings_by_len(self, keybindings, min_len=1):
        max_key_length = len(max(keybindings, key=len))
        def reducer(accum, key_length):
            accum.append([v for k, v in enumerate(keybindings) if len(keybindings[k]) == key_length])
            return accum
        sorted_keybindings = reduce(reducer, range(max_key_length, min_len, -1), [])
        return list(filter(None, sorted_keybindings))

    def get_non_modified_keybindings(self):
        return [k for k in self.keybindings if not self.keybindings[k]['has_modifier']]

    def add_keybinding_to_key_cache(self, to_cache, keybinding, existing_keybindings, key_cache):
        if to_cache in existing_keybindings:
            raise_(KeybindingError, "Invalid key binding '%s', '%s' already used in another key binding" % (keybinding, to_cache))
        else:
            key_cache[to_cache] = True

    def build_multi_key_cache(self):
        keybindings = self.get_non_modified_keybindings()
        sorted_keybindings = self.sort_keybindings_by_len(keybindings)
        def sorted_keybindings_reducer(key_cache, keybinding_list):
            def keybinding_list_reducer(_, keybinding):
                keys = list(keybinding)
                keys.pop()
                def keybinding_reducer(processed_keys, key):
                    processed_keys.append(key)
                    to_cache = ''.join(processed_keys)
                    self.add_keybinding_to_key_cache(to_cache, keybinding, keybindings, key_cache)
                    return processed_keys
                reduce(keybinding_reducer, keys, [])
            reduce(keybinding_list_reducer, keybinding_list, [])
            return key_cache
        self.multi_key_cache = reduce(sorted_keybindings_reducer, sorted_keybindings, {})
