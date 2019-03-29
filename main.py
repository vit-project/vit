#!/usr/bin/env python

import sys
from config_parser import Parser
import report
import application
import pprint
from tasklib import TaskWarrior

pp = pprint.PrettyPrinter()

default_report = 'hot'
if len(sys.argv) > 1:
  default_report = sys.argv[1]

def main():
  task_config = Parser()
  reports = report.generate_all(task_config)
  #pp.pprint(reports)

  application.init_app(task_config, reports, default_report)

if __name__ == '__main__':
  main()
