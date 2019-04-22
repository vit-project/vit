from future.utils import raise_

import os
import re
import shlex
import datetime

from functools import reduce

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import env
from process import Command

SORT_ORDER_CHARACTERS = ['+', '-']
SORT_COLLATE_CHARACTERS = ['/']
DEFAULT_VIT_CONFIG_DIR = '~/.vit'
VIT_CONFIG_FILE = 'config.ini'
FILTER_EXCLUSION_REGEX = re.compile('^limit:')
FILTER_PARENS_REGEX = re.compile('([\(\)])')
CONFIG_BOOLEAN_TRUE_REGEX = re.compile('1|yes|true', re.IGNORECASE)
# TaskParser expects clean hierachies in the TaskWarrior dotted config names.
# However, this is occassionally violated, with a leaf ending in both a string
# value and another branch. The below list contains the config values that
# violate this convention, and transform them into a single additional branch
# of value CONFIG_STRING_LEAVES_DEFAULT_BRANCH
CONFIG_STRING_LEAVES = [
    'color.calendar.due',
    'color.due',
    'color.label',
]
CONFIG_STRING_LEAVES_DEFAULT_BRANCH = 'default'

DEFAULTS = {
    'taskwarrior': {
        'taskrc': '~/.taskrc',
    },
    'vit': {
        'default_keybindings': 'vi',
        'theme': 'default',
    },
    'report': {
        'default_report': 'next',
        'indent_subprojects': True,
    },
}

# strftime() works differently on Windows, test here.
test_datetime = datetime.datetime(1900, 1, 1)
NO_PAD_FORMAT_CODE = '-' if test_datetime.strftime('%-d') == '1' else '#' if test_datetime.strftime('%#d') == '1' else ''

DATE_FORMAT_MAPPING = {
    'm': '%%%sm' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit month number, eg '1', '12'
    'M': '%m',                           # 2 digit month number, eg '01', '12'
    'd': '%%%sd' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit day of month number¸ eg '1', '12'
    'D': '%d',                           # 2 digit day of month number, eg '01', '30'
    'y': '%y',                           # 2 digit year, eg '12', where the century is assumed to be '20', therefore '2012'
    'Y': '%Y',                           # 4 digit year, eg '2015'
    'h': '%%%sH' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit hours, eg '1', '23'
    'H': '%H',                           # 2 digit hours, eg '01', '23'
    'n': '%%%sM' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit minutes, eg '1', '59'
    'N': '%M',                           # 2 digit minutes, eg '01', '59'
    's': '%%%sS' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit seconds, eg '1', '59'
    'S': '%S',                           # 2 digit seconds, eg '01', '59'
    'v': '%%%sU' % NO_PAD_FORMAT_CODE,   # 1 or 2 digit week number, eg '1', '52'
    'V': '%U',                           # 2 digit week number, eg '01', '52'
    'a': '%a',                           # 3-character English day name abbreviation, eg 'mon', 'tue'
    'A': '%A',                           # Complete English day name, eg 'monday', 'tuesday'
    'b': '%b',                           # 3-character English month name abbreviation, eg 'jan', 'feb'
    'B': '%B',                           # Complete English month name, eg 'january', 'february'
    'j': '%%%sj' % NO_PAD_FORMAT_CODE,   # 1, 2 or 3 digit day-of-year number, sometimes referred to as a Julian date, eg '1', '11', or '365'
    'J': '%j',                           # 3 digit day of year number, sometimes referred to as a Julian date, eg '001', '011', or '365'
}

class ConfigParser(object):
    def __init__(self):
        self.config = configparser.SafeConfigParser()
        self.config.optionxform=str
        self.config.read('%s/%s' % (os.path.expanduser('VIT_CONFIG' in env.user and env.user['VIT_CONFIG'] or DEFAULT_VIT_CONFIG_DIR), VIT_CONFIG_FILE))
        self.subproject_indentable = self.is_subproject_indentable()

    def get(self, section, key):
        default = DEFAULTS[section][key]
        try:
            value = self.config.get(section, key)
            return self.transform(key, value, default)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def items(self, section):
        try:
            return self.config.items(section)
        except configparser.NoSectionError:
            return []

    def has_section(self, section):
        return self.config.has_section(section)

    def transform(self, key, value, default):
        if isinstance(default, bool):
            return self.transform_bool(value)
        else:
            return value

    def transform_bool(self, value):
        return True if CONFIG_BOOLEAN_TRUE_REGEX.match(value) else False

    def is_subproject_indentable(self):
        return self.get('report', 'indent_subprojects')

class TaskParser(object):
    def __init__(self, config):
        self.config = config
        self.task_config = []
        self.reports = {}
        self.command = Command(self.config)
        returncode, stdout, stderr = self.command.run('task _show', capture_output=True)
        if returncode == 0:
            lines = list(filter(lambda x: True if x else False, stdout.split("\n")))
            for line in lines:
                hierarchy, values = line.split('=')
                self.task_config.append((hierarchy, values))
        else:
            raise_(RuntimeError, 'Error parsing task config: %s' % stderr)

    def transform_string_leaves(self, hierarchy):
        if hierarchy in CONFIG_STRING_LEAVES:
            hierarchy += '.%s' % CONFIG_STRING_LEAVES_DEFAULT_BRANCH
        return hierarchy

    def filter_to_dict(self, matcher_regex):
        lines = self.filter(matcher_regex)
        return {self.transform_string_leaves(key): value for key, value in lines}

    def filter(self, matcher_regex):
        return list(filter(lambda config_pair: re.match(matcher_regex, config_pair[0]), self.task_config))

    def subtree(self, matcher, walk_subtree=True):
      matcher_regex = matcher
      if walk_subtree:
          matcher_regex = r'%s' % (('^%s' % matcher).replace('.', '\.'))
      full_tree = {}
      lines = self.filter(matcher_regex)
      for (hierarchy, value) in lines:
        hierarchy = self.transform_string_leaves(hierarchy)
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

    def translate_date_markers(self, string):
        return reduce(lambda accum, code: accum.replace(code[0], code[1]), list(DATE_FORMAT_MAPPING.items()), string)

    def get_reports(self):
      reports = {}
      subtree = self.subtree('report.')
      for report, attrs in list(subtree.items()):
        reports[report] = {
            'name': report,
            'subproject_indentable': False,
        }
        if 'columns' in attrs:
          reports[report]['columns'] = attrs['columns'].split(',')
        if 'description' in attrs:
          reports[report]['description'] = attrs['description']
        if 'filter' in attrs:
          # Allows quoted strings.
          # Adjust for missing spaces around parentheses.
          filters = shlex.split(re.sub(FILTER_PARENS_REGEX, r' \1 ', attrs['filter']))
          reports[report]['filter'] = [f for f in filters if not FILTER_EXCLUSION_REGEX.match(f)]
        if 'labels' in attrs:
          reports[report]['labels'] = attrs['labels'].split(',')
        if 'sort' in attrs:
          columns = attrs['sort'].split(',')
          reports[report]['sort'] = [self.parse_sort_column(c) for c in columns]
          reports[report]['subproject_indentable'] = self.is_subproject_indentable(reports[report])
        if 'dateformat' in attrs:
          reports[report]['dateformat'] = self.translate_date_markers(attrs['dateformat'])

        self.reports = reports
      return reports

    def is_subproject_indentable(self, report):
        primary_sort = report['sort'][0]
        return primary_sort[0] == 'project' and primary_sort[1] == 'ascending'

    def get_column_index(self, report, column):
        return self.reports[report]['columns'].index(column)

    def get_column_label(self, report, column):
        column_index = self.get_column_index(report, column)
        return self.reports[report]['labels'][column_index]
