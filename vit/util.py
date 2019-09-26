import os
import sys
import curses
import shlex
from functools import reduce

curses.setupterm()
e3_seq = curses.tigetstr('E3') or b''
clear_screen_seq = curses.tigetstr('clear') or b''

def clear_screen():
    os.write(sys.stdout.fileno(), e3_seq + clear_screen_seq)

def string_to_args(string):
    try:
      return shlex.split(string)
    except ValueError:
      return []

def is_mouse_event(key):
    return not isinstance(key, str)

def uuid_short(uuid):
    return uuid[0:8]

def task_id_or_uuid_short(task):
    return task['id'] or uuid_short(task['uuid'])

def task_pending(task):
    return task['status'] == 'pending'

def task_completed(task):
    return task['status'] == 'completed' or task['status'] == 'deleted'

def project_get_subproject_and_parents(project):
    parts = project.split('.')
    subproject = parts.pop()
    parents = parts if len(parts) > 0 else None
    return subproject, parents

def project_get_root(project):
    return project.split('.')[0] if project else None

def file_to_class_name(file_name):
    words = file_name.split('_')
    return ''.join((w.capitalize() for w in words))

def file_readable(filepath):
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)
