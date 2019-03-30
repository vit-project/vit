from asciimatics.widgets import Frame, MultiColumnListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys
import re
from functools import partial
from tasklib import TaskWarrior
tw = TaskWarrior()

def get_app_width():
  return 80

def task_date(task, attr, fmt='%Y-%m-%d'):
  try:
    return task[attr].strftime(fmt)
  except AttributeError:
    return ''

def wrap_line(text, length=40):
  output = ''
  for x in text.splitlines():
    output += '\n'.join(line.strip() for line in re.findall(r".{1,%s}(?:\s+|$)" % length, x))
  return output

class TaskModel(object):
    def __init__(self, reports, report):

        self.current_task_id = None
        self.reports = reports
        self.report = report
        self.tasks = []

    def add(self, contact):
        pass

    def active_report(self):
        return self.reports[self.report]

    def update_report(self, report):
        self.report = report
        tasks = tw.tasks.filter(*self.active_report()['filter'])
        self.tasks = tasks

    def build_task_row(self, task):
        width = get_app_width()
        desc_width = get_app_width() - 6
        columns = [
          str(task['id']),
          wrap_line(task['description'], desc_width - 6),
          task_date(task, 'scheduled'),
        ]
        return (columns, task['id'])

    def get_summary(self, report=None):
        report = report or self.report
        self.update_report(report)
        summary = []
        for task in self.tasks:
            summary.append(self.build_task_row(task))
        return summary

class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       has_border=False,
                                       )
        self._model = model

        # Create the form for displaying the list of tasks.
        width = get_app_width()
        desc_width = get_app_width() - 6
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            [6, desc_width - 2, 11],
            self._model.get_summary(),
            name="tasks",
            titles=self._model.active_report()['labels'],
            on_change=self._on_pick)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        pass

    def _reload_list(self, new_value=None):
        self._list_view.options = self._model.get_summary()
        self._list_view.value = new_value

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

def task_report(tasks, screen, scene):
    scenes = [
        Scene([ListView(screen, tasks)], -1, name="Tasks"),
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scene)


def init_app(reports, report):
    tasks = TaskModel(reports, report)
    last_scene = None
    while True:
        try:
            Screen.wrapper(partial(task_report, tasks), catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
