import urwid
from util import is_mouse_event

class CommandBar(urwid.Edit):
    """Custom urwid.Edit class for the command bar.
    """
    def __init__(self, **kwargs):
        self.event = kwargs['event']
        self.metadata = None
        kwargs.pop('event')
        return super().__init__(**kwargs)

    def keypress(self, size, key):
        """Overrides Edit.keypress method.
        """
        if is_mouse_event(key):
            return key
        # TODO: Readline edit shortcuts.
        if 'choices' in self.metadata:
            data = {
                'choice': None,
                'metadata': self.get_metadata(),
            }
            if key in self.metadata['choices']:
                data['choice'] = self.metadata['choices'][key]
            self.cleanup()
            self.event.emit('command-bar:keypress', data)
            return None
        elif key in ('enter', 'esc'):
            text = self.get_edit_text()
            data = {
                'key': key,
                'text': text,
                'metadata': self.get_metadata(),
            }
            self.cleanup()
            self.event.emit('command-bar:keypress', data)
            return None
        return super().keypress(size, key)

    def set_edit_text(self, text):
        ret = super().set_edit_text(text)
        self.set_edit_pos(len(text))
        return ret

    def set_command_prompt(self, caption, edit_text=None):
        self.set_caption(caption)
        if edit_text:
            self.set_edit_text(edit_text)

    def activate(self, caption, metadata, edit_text=None):
        self.set_metadata(metadata)
        self.set_command_prompt(caption, edit_text)

    def cleanup(self):
        self.set_caption('')
        self.set_edit_text('')
        self.set_metadata(None)

    def get_metadata(self):
        return self.metadata.copy() if self.metadata else None

    def set_metadata(self, metadata):
        self.metadata = metadata

