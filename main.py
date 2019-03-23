import sys
import config_parser
import report
import application
import pprint
from tasklib import TaskWarrior

pp = pprint.PrettyPrinter()

default_report = 'hot'
if len(sys.argv) > 1:
  default_report = sys.argv[1]

def main():
  task_config = config_parser.parse()
  reports = report.generate_all(task_config)
  #pp.pprint(reports)
  tw = TaskWarrior()
  tasks = tw.tasks.filter(*reports[default_report]['filter'])
  #pp.pprint(tasks)
  application.init_app(tasks)

if __name__ == '__main__':
  main()
