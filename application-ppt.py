from __future__ import unicode_literals
import re
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import VSplit, HSplit, Layout, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style
from functools import partial
from tasklib import TaskWarrior

application = None

def exit(event):
    event.app.exit()

def view_task(task_uuid, event):
  get_app().run_system_command('clear && task %s' % task_uuid)

def edit_task(task_uuid, event):
  get_app().run_system_command('task %s edit' % task_uuid)

def get_app_width():
  return 80

def task_date(task, attr, fmt='%Y-%m-%d'):
  try:
    return task[attr].strftime(fmt)
  except AttributeError:
    return ''

def header_row():
  width = get_app_width()
  desc_width = get_app_width() - 6
  return VSplit([
    Window(FormattedTextControl(text='ID', style='fg:ansiblack'), width=4, align=WindowAlign.LEFT, dont_extend_height=True),
    Window(FormattedTextControl('Description', style='fg:ansiblack'), width=desc_width, align=WindowAlign.LEFT, dont_extend_height=True),
    Window(FormattedTextControl(text='Starts', style='fg:ansiblack'), width=10, align=WindowAlign.LEFT, dont_extend_height=True),
  ], padding=Dimension(preferred=2), style='bg:ansigray')

def hot_report(event):
  app = event.app
  tw = TaskWarrior()
  tasks = tw.tasks.filter('+PENDING', 'priority:H')
  pp.pprint("HOT")
  app.exit()
  init_app(tasks)

def wrap_line(text, length=40):
  output = ''
  for x in text.splitlines():
    output += '\n'.join(line.strip() for line in re.findall(r".{1,%s}(?:\s+|$)" % length, x))
  print(output)
  return output

def build_task_row(task):
  key_bindings = KeyBindings()
  key_bindings.add('enter')(partial(view_task, task['uuid']))
  key_bindings.add('e')(partial(edit_task, task['uuid']))
  width = get_app_width()
  desc_width = get_app_width() - 6
  return VSplit([
    Window(FormattedTextControl(text=str(task['id'])), width=4, align=WindowAlign.LEFT),
    Window(FormattedTextControl(text=wrap_line(task['description'], desc_width), focusable=True, key_bindings=key_bindings, show_cursor=True), width=desc_width, align=WindowAlign.LEFT, wrap_lines=True),
    Window(FormattedTextControl(text=task_date(task, 'scheduled')), width=10, align=WindowAlign.LEFT),
  ], padding=Dimension(preferred=2))

def build_task_list(tasks):
  task_list = [
    header_row(),
  ]
  for task in tasks:
    task_list.append(build_task_row(task))
  return HSplit(task_list)

def init_app(tasks):
  layout = Layout(
      container=build_task_list(tasks),
  )

  # Key bindings.
  kb = KeyBindings()
  kb.add('escape')(exit)
  kb.add('tab')(focus_next)
  kb.add('j')(focus_next)
  kb.add('s-tab')(focus_previous)
  kb.add('k')(focus_previous)
  kb.add('h')(hot_report)


  # Styling.
  style = Style([
    ('button focused', 'bg:#4286f4 bold underline'),
  ])


  # Build a main application object.
  application = Application(
      layout=layout,
      key_bindings=kb,
      style=style,
      full_screen=True)

  application.run()

