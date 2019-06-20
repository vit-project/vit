import urwid

class CommandBar(urwid.Edit):
    """Custom urwid.Edit class for the command bar.
    """
    def __init__(self, **kwargs):
        self.event = kwargs['event']
        self.autocomplete = kwargs['autocomplete']
        self.metadata = None
        self.history = CommandBarHistory()
        kwargs.pop('event')
        kwargs.pop('autocomplete')
        return super().__init__(**kwargs)

    def keypress(self, size, key):
        """Overrides Edit.keypress method.
        """
        # TODO: Readline edit shortcuts.
        if key not in ('tab', 'shift tab'):
            self.autocomplete.deactivate()
        if 'choices' in self.metadata:
            op = self.metadata['op']
            data = {
                'choice': None,
                'metadata': self.get_metadata(),
            }
            if key in self.metadata['choices']:
                data['choice'] = self.metadata['choices'][key]
            self.cleanup(op)
            self.event.emit('command-bar:keypress', data)
            return None
        elif key in ('ctrl a',):
            self.set_edit_pos(0)
            return None
        elif key in ('ctrl e',):
            self.set_edit_pos(len(self.get_edit_text()))
            return None
        elif key in ('up', 'ctrl p'):
            text = self.history.previous(self.metadata['history'])
            if text != False:
                self.set_edit_text(text)
            return None
        elif key in ('down', 'ctrl n'):
            text = self.history.next(self.metadata['history'])
            if text != False:
                self.set_edit_text(text)
            return None
        elif key in ('enter', 'esc'):
            text = self.get_edit_text().strip()
            metadata = self.get_metadata()
            data = {
                'key': key,
                'text': text,
                'metadata': metadata,
            }
            self.cleanup(metadata['op'])
            if text and key in ('enter'):
                self.history.add(metadata['history'], text)
            self.event.emit('command-bar:keypress', data)
            return None
        elif key in ('tab', 'shift tab'):
            if self.is_autocomplete_op():
                text = self.get_edit_text()
                kwargs = {}
                if key in ('shift tab',):
                    kwargs['reverse'] = True
                self.autocomplete.activate(text, self.edit_pos, **kwargs)
            return None
        return super().keypress(size, key)

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
        if edit_text:
            self.set_edit_text(edit_text)

    def activate(self, caption, metadata, edit_text=None):
        self.set_metadata(metadata)
        self.set_command_prompt(caption, edit_text)

    def cleanup(self, command):
        self.set_caption('')
        self.set_edit_text('')
        self.history.cleanup(command)
        self.set_metadata(None)

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

