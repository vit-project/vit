import os
import sys
import curses
import shlex
import six

import version

from functools import reduce

curses.setupterm()
e3_seq = curses.tigetstr('E3') or b''
clear_screen_seq = curses.tigetstr('clear') or b''

def clear_screen():
    os.write(sys.stdout.fileno(), e3_seq + clear_screen_seq)

def is_string(obj):
    if version.PY3:
        return isinstance(obj, str)
    else:
        return isinstance(obj, basestring)

def string_to_args(string):
    return shlex.split(string)

def is_mouse_event(key):
    return not isinstance(key, six.string_types)

def uuid_short(uuid):
    return uuid[0:8]

def format_key_command(command_string, replacements={}):
    for token, replacement in list(replacements.items()):
        command_string = command_string.replace(token, replacement)
    def reducer(accum, char):
        if char == '<':
            accum['in_brackets'] = True
            accum['bracket_string'] = ''
        elif char == '>':
            accum['in_brackets'] = False
            accum['key_command'].append(accum['bracket_string'])
        else:
            if accum['in_brackets']:
                accum['bracket_string'] += char
            else:
                accum['key_command'].append(char)
        return accum
    accum = reduce(reducer, command_string, {'key_command': [], 'in_brackets': False, 'bracket_string': ''})
    return accum['key_command']
