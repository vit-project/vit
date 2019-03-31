import urwid

class CommandBar(urwid.Edit):
    """Custom urwid.Edit class for the command bar.
    """
    def __init__(self, **kwargs):
        self.event = kwargs['event']
        kwargs.pop('event')
        return super().__init__(**kwargs)

    def keypress(self, size, key):
        """Overrides Edit.keypress method.
        """
        # TODO: Readline edit shortcuts.
        if key in ('enter', 'esc'):
            data = self.get_edit_text()
            self.set_caption('')
            self.set_edit_text('')
            self.event.emit('command-bar:keypress', {'key': key, 'data': data})
            return True
        return super().keypress(size, key)

