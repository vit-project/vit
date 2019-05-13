#!/usr/bin/env python

import sys

from config_parser import ConfigParser, TaskParser
from application import Application
from tasklib import TaskWarrior

def main():
  config = ConfigParser()
  task_config = TaskParser(config)
  reports = task_config.get_reports()
  default_report = sys.argv[1] if len(sys.argv) > 1 else config.get('report', 'default_report')

  Application(config, task_config, reports, default_report)

if __name__ == '__main__':
  main()
