import urwid

class MultiWidget(urwid.Widget):
    """A widget container that presents one child widget at a time."""

    #: A dict containing all widgets.
    widgets = {}

    #: Name of the current widget.
    current = None

    def __init__(self):
        self.widgets = {}
        self.current = None

    def add_widget(self, name, widget):
        """Adds a widget by name."""
        self.widgets[name] = widget

    def show_widget(self, name):
        assert 0 < len(self.widgets)
        self.current = name
        self._invalidate()

    @property
    def widget_count(self):
        """The function name is pretty much self-explanatory."""
        return len(self.widgets)

    @property
    def current_widget(self):
        """Returns a widget that is currently being rendered. If the widget
        list is empty, it returns None."""
        if self.current and self.current in self.widgets:
            return self.widgets[self.current]
        else:
            return None

    def selectable(self):
        """It appears ``selectable()`` must return ``True`` in order to get any
        key input."""

        return True

    def rows(self, size, focus=False):
        return self.current_widget.rows(size, focus) if self.current_widget is not None else 0

    def render(self, size, focus=False):
        assert self.current_widget is not None

        return self.current_widget.render(size, focus)

    def keypress(self, size, key):
        """Passes key inputs to the current widget. If the current widget is
        ``None`` then it returns the given key input so that
        ``unhandled_input`` function can handle it."""

        if self.current_widget is not None:
            return self.current_widget.keypress(size, key)
        else:
            return key

    def mouse_event(self, size, event, button, col, row, focus):
        if self.current_widget is not None:
            return self.current_widget.mouse_event(
                size, event, button, col, row, focus)
        else:
            return False
