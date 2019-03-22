import config_parser
import report
import application
import pprint
from tasklib import TaskWarrior

pp = pprint.PrettyPrinter()

def main():
  task_config = config_parser.parse()
  reports = report.generate_all(task_config)
  #pp.pprint(reports)
  default_report = 'hot'
  tw = TaskWarrior()
  tasks = tw.tasks.filter(*reports[default_report]['filter'])
  #pp.pprint(tasks)
  application.build_task_list(tasks)

if __name__ == '__main__':
  main()
