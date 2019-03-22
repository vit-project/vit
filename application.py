from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import VSplit, HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from functools import partial

import pprint

pp = pprint.PrettyPrinter()

def exit_clicked(key):
    get_app().exit()

def view_task(task_uuid, event):
  get_app().run_system_command('clear && task %s' % task_uuid)

def edit_task(task_uuid, event):
  get_app().run_system_command('task %s edit' % task_uuid)

def build_task_row(task):
  key_bindings = KeyBindings()
  key_bindings.add('enter')(partial(view_task, task['uuid']))
  key_bindings.add('e')(partial(edit_task, task['uuid']))
  return Window(FormattedTextControl(text=task['description'], focusable=True, key_bindings=key_bindings, show_cursor=True), dont_extend_height=True)

def build_task_list(tasks):
  task_list = []
  for task in tasks:
    task_list.append(build_task_row(task))
  root_container = HSplit(task_list)

  layout = Layout(
      container=root_container,
  )


  # Key bindings.
  kb = KeyBindings()
  kb.add('escape')(exit_clicked)
  kb.add('tab')(focus_next)
  kb.add('j')(focus_next)
  kb.add('s-tab')(focus_previous)
  kb.add('k')(focus_previous)


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

