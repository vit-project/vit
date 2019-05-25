import re

import urwid

from vit.base_list_box import BaseListBox

CURLY_BRACES_REGEX = re.compile("[{}]")
SPECIAL_KEY_SUBSTITUTIONS = {
    '<Colon>': ':',
    '<Equals>': '=',
}

class SelectableHelpRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    This class has been slightly modified, but essentially corresponds to this class posted on stackoverflow.com:
    https://stackoverflow.com/questions/52106244/how-do-you-combine-multiple-tui-forms-to-write-more-complex-applications#answer-52174629"""

    def __init__(self, column_widths, data, position, *, space_between=2):
        self.data = data
        self.position = position
        self._columns = urwid.Columns([
            (column_widths['type'], urwid.Text(self.data[0], align='left')),
            (column_widths['keys'], urwid.Text(self.data[1], align='left')),
            urwid.Text(self.data[2], align='left'),
        ], dividechars=space_between)
        self.row = urwid.AttrMap(self._columns, '', 'reveal focus')

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

    def __repr__(self):
        return "{}(type={}, keys={}, desc={})".format(self.__class__.__name__, self.data[0], self.data[1], self.data[2])

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

class HelpListBox(BaseListBox):
    """Custom ListBox class for help.
    """

    def __init__(self, body, keybindings, event=None, request_reply=None, action_manager=None):
        self.keybindings = keybindings
        return super().__init__(body, event=event, request_reply=request_reply, action_manager=action_manager)

    def register_managed_actions(self):
        super().register_managed_actions()
        self.action_manager_registrar.register('GLOBAL_ESCAPE', self.exit_help)
        self.action_manager_registrar.register('QUIT_WITH_CONFIRM', self.exit_help)
        self.action_manager_registrar.register('QUIT', self.exit_help)

    def calculate_column_widths(self, entries):
        column_widths = {
            'type': 0,
            'keys': 0,
        }
        for entry in entries:
            type_len = len(entry[0])
            keys_len = len(entry[1])
            if type_len > column_widths['type']:
                column_widths['type'] = type_len
            if keys_len > column_widths['keys']:
                column_widths['keys'] = keys_len
        return column_widths

    def reload_entries(self, entries):
        column_widths = self.calculate_column_widths(entries)
        rows = [SelectableHelpRow(column_widths, row, idx) for idx, row in enumerate(entries)]
        self.list_walker[:] = rows
        if len(self.list_walker) > 0:
            self.set_focus(0)

    def exit_help(self, data):
        self.event.emit("help:exit")

    def eat_other_keybindings(self):
        return True

class Help(object):
    """Generates help list/display.
    """
    def __init__(self, keybinding_parser, actions, event=None, request_reply=None, action_manager=None):
        self.keybinding_parser = keybinding_parser
        self.actions = actions
        self.event = event
        self.request_reply = request_reply
        self.action_manager = action_manager
        self.keybindings = self.keybinding_parser.get_keybindings()
        sections = self.build_default_keybinding_data()
        sections = self.add_custom_help(sections)
        self.compose_entries(sections)
        self.build_help_widget()

    def autocomplete_entries(self):
        return [
            'help',
            'help command',
            'help global',
            'help help',
            'help navigation',
            'help report',
        ]

    def update(self, filter_args):
        entries = self.filter_entries(filter_args)
        self.listbox.reload_entries(entries)
        return self.widget

    def filter_entries(self, filter_args):
        if len(filter_args) > 0:
            args_regex = re.compile('.*(%s).*' % '|'.join(filter_args))
            return [(section, keys, description) for section, keys, description, search_phrase in self.entries if args_regex.match(search_phrase)]
        else:
            return [(section, keys, description) for section, keys, description, _ in self.entries]

    def compose_entries(self, sections):
        self.entries = []
        for section in self.keybinding_parser.sections:
            for keys, description in sections[section]:
                self.add_entry(section, keys, description)
        for keys, description in sections['help']:
            self.add_entry('help', keys, description)

    def add_entry(self, section, keys, description):
        self.entries.append((section, keys, description, ' '.join([section, keys, description])))

    # TODO: This does not pull data from keybinding overrides in config.ini
    # yet.
    def build_default_keybinding_data(self):
        sections = {}
        for section in self.keybinding_parser.sections:
            sections[section] = []
            for keys, action in self.keybinding_parser.items(section):
                action = re.sub(CURLY_BRACES_REGEX, '', action)
                keys = self.special_key_substitutions(keys)
                if action in self.actions:
                    sections[section].append((keys, self.actions[action]['description']))
        return sections

    def add_custom_help(self, sections):
        sections['command'] += [
            (':q', 'Quit the application'),
            (':![rw] STRING', "Execute STRING in shell. 'r' re-reads, 'w' waits"),
            (':s/OLD/NEW/', "Change OLD to NEW in the current task's description"),
            (':%s/OLD/NEW/', "Change OLD to NEW in the current task's description"),
        ]
        sections['navigation'] += [
            (':N', 'Move to task number N'),
        ]
        sections['report'] += [
            (':REPORT', 'Display REPORT (supports tab completion)'),
            (':REPORT FILTER', 'Display REPORT with FILTER (supports tab completion)'),
        ]
        sections['help'] = [
            (':help', 'View the whole help file'),
            (':help command', 'View help about commands'),
            (':help global', 'View help global actions'),
            (':help help', 'View help about help'),
            (':help navigation', 'View help about navigation'),
            (':help report', 'View help about reports'),
            (':help PATTERN', 'View help file lines matching PATTERN'),
        ]
        return sections

    def special_key_substitutions(self, keys):
        for key, sub in SPECIAL_KEY_SUBSTITUTIONS.items():
            keys = keys.replace(key, sub)
        return keys

    def build_help_widget(self):
        self.listbox = HelpListBox(urwid.SimpleFocusListWalker([]), self.keybinding_parser.keybindings, event=self.event, request_reply=self.request_reply, action_manager=self.action_manager)
        self.widget = urwid.Frame(
            self.listbox,
            header=urwid.Pile([
                urwid.Text("Press '<Esc>' or 'q' to exit", align='center'),
                # TODO: Remove this when keybinding overrides are shown.
                urwid.Text("NOTE: Keybinding overrides in config.ini not shown", align='center'),
                urwid.Text(''),
            ]),
        )
