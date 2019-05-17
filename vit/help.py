import re

CURLY_BRACES_REGEX = re.compile("[{}]")
SPECIAL_KEY_SUBSTITUTIONS = {
    '<Colon>': ':',
    '<Equals>': '=',
}

class Help(object):
    """Generates help list/display.
    """
    def __init__(self, keybinding_parser, actions):
        self.keybinding_parser = keybinding_parser
        self.actions = actions
        self.keybindings = self.keybinding_parser.get_keybindings()
        sections = self.build_default_keybinding_data()
        sections = self.add_custom_help(sections)
        self.compose_entries(sections)

    def filter_entries(self, filter_args):
        if len(filter_args) > 0:
            args_regex = re.compile('(%s)' % '|'.join(filter_args))
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
            (':h', 'View the whole help file'),
            (':h command', 'View help about commands'),
            (':h help', 'View help about help'),
            (':h navigation', 'View help about navigation'),
            (':h report', 'View help about reports'),
            (':h PATTERN', 'View help file lines matching PATTERN'),
        ]
        return sections

    def special_key_substitutions(self, keys):
        for key, sub in SPECIAL_KEY_SUBSTITUTIONS.items():
            keys = keys.replace(key, sub)
        return keys
