import os
import re

from task import TaskCommand

class Parser(object):
    def __init__(self):
        self.config = []
        self.command = TaskCommand()
        returncode, stdout, stderr = self.command.run('task _show')
        if returncode == 0:
            lines = list(filter(lambda x: True if x else False, stdout.split("\n")))
            for line in lines:
                hierarchy, values = line.split("=")
                self.config.append((hierarchy, values))
        else:
            raise "Error parsing task config: %s" % stderr

    def subtree(self, matcher, walk_subtree=False):
      full_tree = {}
      lines = list(filter(lambda config_pair: re.match(matcher, config_pair[0]), self.config))
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

    def reports(self):
      reports = {}
      subtree = self.subtree(r'^report\.')
      for report, attrs in list(subtree['report'].items()):
        reports[report] = {}
        if 'columns' in attrs:
          reports[report]['columns'] = attrs['columns'].split(',')
        if 'description' in attrs:
          reports[report]['description'] = attrs['description']
        if 'filter' in attrs:
          # Allows quoted strings.
          reports[report]['filter'] = [p for p in re.split("( |\\\".*?\\\"|'.*?')", attrs['filter']) if p.strip()]
        if 'labels' in attrs:
          reports[report]['labels'] = attrs['labels'].split(',')
        if 'sort' in attrs:
          reports[report]['sort'] = attrs['sort'].split(',')
      return reports
