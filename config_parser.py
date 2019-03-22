import os
import re

def parse():
  config = []
  cmd_output = os.popen('task _show').read()
  lines = list(filter(lambda x: True if x else False, cmd_output.split("\n")))
  for line in lines:
    hierarchy, values = line.split("=")
    config.append((hierarchy, values))
  return config

def subtree(task_config, matcher):
  subtree = {}
  lines = list(filter(lambda config_pair: re.match(matcher, config_pair[0]), task_config))
  for (hierarchy, value) in lines:
    parts = hierarchy.split('.')
    tree_location = subtree
    while True:
      if len(parts):
        part = parts.pop(0)
        if part not in tree_location:
          tree_location[part] = {} if len(parts) else value
        tree_location = tree_location[part]
      else:
        break
  return subtree
