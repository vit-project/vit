import urwid
from vit.readline import Readline

class CommandBar(urwid.Edit):
    """Custom urwid.Edit class for the command bar.
    """
    def __init__(self, **kwargs):
        self.event = kwargs.pop('event')
        self.autocomplete = kwargs.pop('autocomplete')
        self.abort_backspace = kwargs.pop('abort_backspace')
        self.metadata = None
        self.history = CommandBarHistory()
        self.readline = Readline(self)
        return super().__init__(**kwargs)

    def keypress(self, size, key):
        """Overrides Edit.keypress method.
        """
        if key not in ('tab', 'shift tab'):
            self.autocomplete.deactivate()
        if 'choices' in self.metadata:
            self.quit({'choice': self.metadata['choices'].get(key)})
            return None
        elif key in ('up',):
            self.readline.keypress('ctrl p')
            return None
        elif key in ('down',):
            self.readline.keypress('ctrl n')
            return None
        elif key in ('enter', 'esc'):
            text = self.get_edit_text().strip()
            if text and key == 'enter':
                self.history.add(self.metadata['history'], text)
            self.quit({'key': key, 'text': text})
            return None
        elif key in ('tab', 'shift tab'):
            if self.is_autocomplete_op():
                text = self.get_edit_text()
                kwargs = {}
                if key in ('shift tab',):
                    kwargs['reverse'] = True
                self.autocomplete.activate(text, self.edit_pos, **kwargs)
            return None
        elif key in self.readline.keys():
            return self.readline.keypress(key)
        elif self.is_aborting_backspace(key):
            self.quit({'key': key})
            return None
        return super().keypress(size, key)

    def is_aborting_backspace(self, key):
        return key == 'backspace' and self.abort_backspace and not self.get_edit_text()

    def is_autocomplete_op(self):
        return self.metadata['op'] not in ['search-forward', 'search-reverse']

    def set_edit_text(self, text, edit_pos=None):
        ret = super().set_edit_text(text)
        if not edit_pos:
            edit_pos = len(text)
        self.set_edit_pos(edit_pos)
        return ret

    def set_command_prompt(self, caption, edit_text=None):
        self.set_caption(caption)
        if edit_text is not None:
            self.set_edit_text(edit_text)

    def activate(self, caption, metadata, edit_text=None):
        self.set_metadata(metadata)
        self.set_command_prompt(caption, edit_text)

    def deactivate(self):
        self.set_command_prompt('', '')
        self.history.cleanup(self.metadata['op'])
        self.set_metadata(None)

    def quit(self, metadata_args={}):
        data = {'metadata': self.get_metadata(), **metadata_args}
        self.deactivate()
        self.event.emit('command-bar:keypress', data)  # remove focus from command bar

    def get_metadata(self):
        return self.metadata.copy() if self.metadata else None

    def prepare_metadata(self, metadata):
        if metadata:
            if 'history' not in metadata:
                metadata['history'] = metadata['op']
        return metadata

    def set_metadata(self, metadata):
        self.metadata = self.prepare_metadata(metadata)

    def set_edit_text_callback(self):
        return self.set_edit_text

class CommandBarHistory(object):
    """Holds command-specific history for the command bar.
    """
    def __init__(self):
        self.commands = {}
        self.scrolling = False

    def add(self, command, text):
        if not self.exists(command):
            self.commands[command] = {'items': ['']}
        self.commands[command]['items'].insert(len(self.get_items(command)) - 1, text)
        self.set_scrolling(command, False)

    def previous(self, command):
        if self.exists(command):
            if not self.scrolling:
                self.set_scrolling(command, True)
                return self.current(command)
            elif self.get_idx(command) > 0:
                self.move_idx(command, -1)
                return self.current(command)
        return False

    def next(self, command):
        if self.exists(command) and self.scrolling and self.get_idx(command) < self.last_idx(command):
            self.move_idx(command, 1)
            return self.current(command)
        return False

    def cleanup(self, command):
        self.set_scrolling(command, False)

    def get_items(self, command):
        return self.commands[command]['items']

    def get_idx(self, command):
        return self.commands[command]['idx']

    def set_idx(self, command, idx):
        self.commands[command]['idx'] = idx

    def set_scrolling(self, command, scroll):
        if self.exists(command):
            # Don't count the ending empty string when setting the initial
            # index for scrolling to start.
            self.set_idx(command, self.last_idx(command) - 1)
        self.scrolling = scroll

    def move_idx(self, command, increment):
        self.set_idx(command, self.get_idx(command) + increment)

    def exists(self, command):
        return command in self.commands

    def current(self, command):
        return self.get_items(command)[self.get_idx(command)] if self.exists(command) else False

    def last_idx(self, command):
        return len(self.get_items(command)) - 1 if self.exists(command) else None

