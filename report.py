import config_parser
import re

def generate_all(task_config):
  reports = {}
  subtree = task_config.subtree(r'^report\.')
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
