class Actions(object):

    def __init__(self, action_registry):
        self.action_registry = action_registry

    def register(self):
        self.action_registrar = self.action_registry.get_registrar()
        # Global.
        self.action_registrar.register('QUIT', 'Quit the application')
        self.action_registrar.register('QUIT_WITH_CONFIRM', 'Quit the application, after confirmation')
        self.action_registrar.register('GLOBAL_ESCAPE', 'Top-level escape function')
        self.action_registrar.register('REFRESH', 'Refresh the current report')
        self.action_registrar.register('TASK_ADD', 'Add a task (supports tab completion)')
        self.action_registrar.register('REPORT_FILTER', 'Filter current report using provided FILTER arguments (supports tab completion)')
        self.action_registrar.register('TASK_UNDO', 'Undo last task change')
        self.action_registrar.register('TASK_SYNC', 'Synchronize with configured taskd server')
        self.action_registrar.register('COMMAND_BAR_EX', "Open the command bar in 'ex' mode")
        self.action_registrar.register('COMMAND_BAR_EX_TASK_READ_WAIT', "Open the command bar in 'ex' mode with '!rw task ' appended")
        self.action_registrar.register('COMMAND_BAR_SEARCH_FORWARD', 'Search forward for provided STRING')
        self.action_registrar.register('COMMAND_BAR_SEARCH_REVERSE', 'Search reverse for provided STRING')
        self.action_registrar.register('COMMAND_BAR_SEARCH_NEXT', 'Search next')
        self.action_registrar.register('COMMAND_BAR_SEARCH_PREVIOUS', 'Search previous')
        self.action_registrar.register('COMMAND_BAR_TASK_CONTEXT', 'Set task context')
        self.action_registrar.register(self.action_registry.noop_action_name, 'Used to disable a default keybinding action')
        # List.
        self.action_registrar.register('LIST_UP', 'Move list focus up one entry')
        self.action_registrar.register('LIST_DOWN', 'Move list focus down one entry')
        self.action_registrar.register('LIST_PAGE_UP', 'Move list focus up one page')
        self.action_registrar.register('LIST_PAGE_DOWN', 'Move list focus down one page')
        self.action_registrar.register('LIST_HOME', 'Move list focus to top of the list')
        self.action_registrar.register('LIST_END', 'Move list focus to bottom of the list')
        self.action_registrar.register('LIST_SCREEN_TOP', 'Move list focus to top of the screen')
        self.action_registrar.register('LIST_SCREEN_MIDDLE', 'Move list focus to middle of the screen')
        self.action_registrar.register('LIST_SCREEN_BOTTOM', 'Move list focus to bottom of the screen')
        self.action_registrar.register('LIST_FOCUS_VALIGN_CENTER', 'Move focused item to center of the screen')
        # Task.
        self.action_registrar.register('TASK_ANNOTATE', 'Add an annotation to a task')
        self.action_registrar.register('TASK_DELETE', 'Delete task')
        self.action_registrar.register('TASK_DENOTATE', 'Denotate a task')
        self.action_registrar.register('TASK_MODIFY', 'Modify task (supports tab completion)')
        self.action_registrar.register('TASK_START_STOP', 'Start/stop task')
        self.action_registrar.register('TASK_DONE', 'Mark task done')
        self.action_registrar.register('TASK_PRIORITY', 'Modify task priority')
        self.action_registrar.register('TASK_PROJECT', 'Modify task project (supports tab completion)')
        self.action_registrar.register('TASK_TAGS', 'Modify task tags (supports tab completion, +TAG adds, -TAG removes)')
        self.action_registrar.register('TASK_WAIT', 'Wait a task')
        self.action_registrar.register('TASK_EDIT', 'Edit a task via the default editor')
        self.action_registrar.register('TASK_SHOW', 'Show task details')

    def get(self):
        return self.action_registry.actions
