from shutil import copyfile

import os
import re
import shlex
import datetime

from functools import reduce

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from vit import env
from vit.process import Command

SORT_ORDER_CHARACTERS = ['+', '-']
SORT_COLLATE_CHARACTERS = ['/']
VIT_CONFIG_FILE = 'config.ini'
FILTER_EXCLUSION_REGEX = re.compile('^limit:')
FILTER_PARENS_REGEX = re.compile('([\(\)])')
CONFIG_BOOLEAN_TRUE_REGEX = re.compile('1|yes|true', re.IGNORECASE)
# TaskParser expects clean hierarchies in the Taskwarrior dotted config names.
# However, this is occasionally violated, with a leaf ending in both a string
# value and another branch. The below list contains the config values that
# violate this convention, and transform them into a single additional branch
# of value CONFIG_STRING_LEAVES_DEFAULT_BRANCH
CONFIG_STRING_LEAVES = [
    'color.calendar.due',
    'color.due',
    'color.label',
    'dateformat',
]
CONFIG_STRING_LEAVES_DEFAULT_BRANCH = 'default'

DEFAULTS = {
    'taskwarrior': {
        'taskrc': '~/.taskrc',
    },
    'vit': {
        'default_keybindings': 'vi',
        'theme': 'default',
        'confirmation': True,
        'wait': True,
        'mouse': False,
        'abort_backspace': False,
    },
    'report': {
        'default_report': 'next',
        'default_filter_only_report': 'next',
        'indent_subprojects': True,
        'row_striping': True,
    },
    'marker': {
        'enabled': True,
        'header_label': '',
        'columns': 'all',
        'require_color': True,
        'include_subprojects': True,
    },
    'color': {
        'enabled': True,
        'include_subprojects': True,
        'none_label': '[NONE]',
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
    def __init__(self, loader):
        self.loader = loader
        self.config = configparser.SafeConfigParser()
        self.config.optionxform=str
        self.user_config_dir = self.loader.user_config_dir
        self.user_config_filepath = '%s/%s' % (self.user_config_dir, VIT_CONFIG_FILE)
        if not self.config_file_exists(self.user_config_filepath):
            self.optional_create_config_file(self.user_config_filepath)
        self.taskrc_path = self.get_taskrc_path()
        self.validate_taskrc()
        self.config.read(self.user_config_filepath)
        self.defaults = DEFAULTS
        self.set_config_data()

    def set_config_data(self):
        self.subproject_indentable = self.is_subproject_indentable()
        self.row_striping_enabled = self.is_row_striping_enabled()
        self.confirmation_enabled = self.is_confirmation_enabled()
        self.wait_enabled = self.is_wait_enabled()
        self.mouse_enabled = self.is_mouse_enabled()

    def validate_taskrc(self):
        try:
            open(self.taskrc_path, 'r').close()
        except FileNotFoundError:
            message = """
%s not found.

VIT requires a properly configured TaskWarrior instance in the current
environment. Execute the 'task' binary with no arguments to initialize a new
configuration.
""" % (self.taskrc_path)
            print(message)
            exit(1)

    def config_file_exists(self, filepath):
        try:
            open(filepath, 'r').close()
            return True
        except FileNotFoundError:
            return False

    def optional_create_config_file(self, filepath):
        prompt = "%s doesn't exist, create? (y/n): " % filepath
        try:
            answer = input(prompt)
        except:
            answer = raw_input(prompt)
        if answer in ['y', 'Y']:
            self.create_config_file(filepath)
            prompt = "\n%s created. This is the default user configuration file. \n\nIt is heavily commented with explanations and lists the default values for all available user configuration variables. Check it out!\n\nPress enter to continue..." % filepath
            try:
                input(prompt)
            except:
                raw_input(prompt)

    def create_config_file(self, filepath):
        dirname = os.path.dirname(filepath)
        try:
            os.mkdir(dirname)
        except FileExistsError:
            pass
        basedir = os.path.dirname(os.path.realpath(__file__))
        copyfile('%s/config/config.sample.ini' % basedir, filepath)

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

    def get_taskrc_path(self):
        return os.path.expanduser('TASKRC' in env.user and env.user['TASKRC'] or self.get('taskwarrior', 'taskrc'))

    def is_subproject_indentable(self):
        return self.get('report', 'indent_subprojects')

    def is_row_striping_enabled(self):
        return self.get('report', 'row_striping')

    def is_confirmation_enabled(self):
        return self.get('vit', 'confirmation')

    def is_wait_enabled(self):
        return self.get('vit', 'wait')

    def is_mouse_enabled(self):
        return self.get('vit', 'mouse')

class TaskParser(object):
    def __init__(self, config):
        self.config = config
        self.task_config = []
        self.projects = []
        self.contexts = {}
        self.reports = {}
        self.disallowed_reports = [
            'timesheet',
        ]
        self.command = Command(self.config)
        self.get_task_config()
        self.get_projects()
        self.set_config_data()

    def set_config_data(self):
        self.print_empty_columns = self.is_truthy(self.subtree('print.empty.columns'))
        self.priority_values = self.get_priority_values()

    def get_task_config(self):
        self.task_config = []
        returncode, stdout, stderr = self.command.run('task _show', capture_output=True)
        if returncode == 0:
            lines = list(filter(lambda x: True if x else False, stdout.split("\n")))
            for line in lines:
                hierarchy, values = line.split('=', maxsplit=1)
                self.task_config.append((hierarchy, values))
        else:
            raise RuntimeError('Error parsing task config: %s' % stderr)

    def get_active_context(self):
        returncode, stdout, stderr = self.command.run('task _get rc.context', capture_output=True)
        if returncode == 0:
            return stdout.strip()
        else:
            raise RuntimeError('Error retrieving active context: %s' % stderr)

    def get_projects(self):
        returncode, stdout, stderr = self.command.run('task _projects', capture_output=True)
        if returncode == 0:
            self.projects = stdout.split("\n")
            # Ditch the trailing newline.
            self.projects.pop()
        else:
            raise RuntimeError('Error parsing task projects: %s' % stderr)

    def get_priority_values(self):
        return self.subtree('uda.priority.values').split(',')

    def transform_string_leaves(self, hierarchy):
        if hierarchy in CONFIG_STRING_LEAVES:
            hierarchy += '.%s' % CONFIG_STRING_LEAVES_DEFAULT_BRANCH
        return hierarchy

    def filter_to_dict(self, matcher_regex):
        lines = self.filter(matcher_regex)
        return {key: value for key, value in lines}

    def filter(self, matcher_regex):
        return list(filter(lambda config_pair: re.match(matcher_regex, config_pair[0]), self.task_config))

    def subtree(self, matcher, walk_subtree=True):
      matcher_regex = matcher
      if walk_subtree:
          matcher_regex = r'%s' % (('^%s' % matcher).replace('.', '\.'))
      full_tree = {}
      lines = self.filter(matcher_regex)
      for (hierarchy, value) in lines:
        # NOTE: This is necessary in order to convert Taskwarrior's dotted
        # config syntax into a full tree, as some leaves are both branches
        # and leaves.
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

    def get_contexts(self):
        contexts = {}
        self.get_task_config()
        subtree = self.subtree('context.')
        for context, filters in list(subtree.items()):
            filters = shlex.split(re.sub(FILTER_PARENS_REGEX, r' \1 ', filters))
            contexts[context] = {
                'filter': [f for f in filters if not FILTER_EXCLUSION_REGEX.match(f)],
            }
        self.contexts = contexts
        return self.contexts

    def get_reports(self):
      reports = {}
      subtree = self.subtree('report.')
      for report, attrs in list(subtree.items()):
        if report in self.disallowed_reports:
            continue
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
        else:
          reports[report]['labels'] = [ column.title() for column in attrs['columns'].split(',') ]
        if 'sort' in attrs:
          columns = attrs['sort'].split(',')
          reports[report]['sort'] = [self.parse_sort_column(c) for c in columns]
        if 'dateformat' in attrs:
          reports[report]['dateformat'] = self.translate_date_markers(attrs['dateformat'])

        self.reports = reports
        # Another pass is needed after all report data has been parsed.
        for report_name, report in self.reports.items():
            self.reports[report_name] = self.rectify_report(report_name, report)
      return self.reports

    def rectify_report(self, report_name, report):
        report['subproject_indentable'] = self.has_project_column(report_name) and self.has_primary_project_ascending_sort(report)
        return report

    def is_truthy(self, value):
        value = str(value)
        return value.lower() in ['y', 'yes', 'on', 'true', '1']

    def has_project_column(self, report_name):
        return self.get_column_index(report_name, 'project') is not None

    def has_primary_project_ascending_sort(self, report):
        try:
            primary_sort = report['sort'][0]
        except KeyError:
            return False

        return primary_sort[0] == 'project' and primary_sort[1] == 'ascending'

    def get_column_index(self, report_name, column):
        return self.reports[report_name]['columns'].index(column) if column in self.reports[report_name]['columns'] else None

    def get_column_label(self, report_name, column):
        column_index = self.get_column_index(report_name, column)
        return self.reports[report_name]['labels'][column_index]
