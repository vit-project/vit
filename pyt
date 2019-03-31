#!/usr/bin/env python

import sys

import config
from config_parser import Parser
from application import Application
from tasklib import TaskWarrior

default_report = sys.argv[1] if len(sys.argv) > 1 else config.default_report

def main():
  task_config = Parser()
  reports = task_config.reports()

  Application(task_config, reports, default_report)

if __name__ == '__main__':
  main()
