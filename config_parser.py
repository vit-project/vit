from future.utils import raise_

import os
import re
import shlex
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import env
from process import Command

SORT_ORDER_CHARACTERS = ['+', '-']
SORT_COLLATE_CHARACTERS = ['/']
DEFAULT_VIT_CONFIG = '~/.vit/vit.conf'
FILTER_EXCLUSION_REGEX = re.compile("^limit:")

DEFAULTS = {
    'taskwarrior': {
        'taskrc': '~/.taskrc',
    },
    'report': {
        'default_report': 'next',
    },
}

class ConfigParser(object):
    def __init__(self):
        self.config = configparser.SafeConfigParser()
        self.config.read(os.path.expanduser('VIT_CONFIG' in env.user and env.user['VIT_CONFIG'] or DEFAULT_VIT_CONFIG))

    def get(self, section, key):
        try:
            return self.config.get(section, key)
        except configparser.NoOptionError:
            return DEFAULTS[section][key]

    def items(self, section):
        try:
            return self.config.items(section)
        except configparser.NoSectionError:
            return []

    def has_section(self, section):
        return self.config.has_section(section)

class TaskParser(object):
    def __init__(self, config):
        self.config = config
        self.task_config = []
        self.command = Command(self.config)
        returncode, stdout, stderr = self.command.run('task _show', capture_output=True)
        if returncode == 0:
            lines = list(filter(lambda x: True if x else False, stdout.split("\n")))
            for line in lines:
                hierarchy, values = line.split("=")
                self.task_config.append((hierarchy, values))
        else:
            raise_(RuntimeError, "Error parsing task config: %s" % stderr)

    def subtree(self, matcher, walk_subtree=True):
      matcher_regex = matcher
      if walk_subtree:
          matcher_regex = r'%s' % (('^%s' % matcher).replace('.', '\.'))
      full_tree = {}
      lines = list(filter(lambda config_pair: re.match(matcher_regex, config_pair[0]), self.task_config))
      for (hierarchy, value) in lines:
        parts = hierarchy.split('.')
        tree_location = full_tree
        while True:
          if len(parts):
            part = parts.pop(0)
            if part not in tree_location:
              tree_location[part] = {} if len(parts) else value
            tree_location = tree_location[part]
          else:
            break
      if walk_subtree:
          parts = matcher.split('.')
          subtree = full_tree
          while True:
            if len(parts):
              part = parts.pop(0)
              if part in subtree:
                  subtree = subtree[part]
            else:
              return subtree
      else:
        return full_tree

    def parse_sort_column(self, column_string):
        order = collate = None
        parts = list(column_string)
        while True:
            if len(parts):
                letter = parts.pop()
                if letter in SORT_ORDER_CHARACTERS:
                    order = letter == '+' and 'ascending' or 'descending'
                elif letter in SORT_COLLATE_CHARACTERS:
                    collate = True
                else:
                    parts.append(letter)
                    break
            else:
                break
        column = ''.join(parts)
        return (column, order, collate)

    def reports(self):
      reports = {}
      subtree = self.subtree('report.')
      for report, attrs in list(subtree.items()):
        reports[report] = {}
        if 'columns' in attrs:
          reports[report]['columns'] = attrs['columns'].split(',')
        if 'description' in attrs:
          reports[report]['description'] = attrs['description']
        if 'filter' in attrs:
          # Allows quoted strings.
          filters = shlex.split(attrs['filter'])
          reports[report]['filter'] = [f for f in filters if not FILTER_EXCLUSION_REGEX.match(f)]
        if 'labels' in attrs:
          reports[report]['labels'] = attrs['labels'].split(',')
        if 'sort' in attrs:
          columns = attrs['sort'].split(',')
          reports[report]['sort'] = [self.parse_sort_column(c) for c in columns]
      return reports
