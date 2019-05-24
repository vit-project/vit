import urwid

from vit import util
from vit.base_list_box import BaseListBox

OVERLAY_WIDTH = 50
OVERLAY_HEIGHT = 15

class AnnotationFrame(urwid.Frame):
    def __init__(self, body, **kwargs):
        self.listbox = body.original_widget
        return super().__init__(body, **kwargs)
    def keypress(self, size, key):
        """Overrides Frame.keypress method.
        """
        if key in ('tab', 'shift tab'):
            self.focus_position = self.focus_position == 'body' and 'footer' or 'body'
            self.listbox.update_focus_blur(self.focus_position == 'body' and 'focus' or 'blur')
            return None
        return super().keypress(size, key)

class AnnotationListBox(BaseListBox):
    """Maps denotation list shortcuts to default ListBox class.
    """

    def __init__(self, body, event=None, request_reply=None, action_manager=None):
        super().__init__(body, event=event, request_reply=request_reply, action_manager=action_manager)
        self.init_event_listeners()

    def list_action_executed(self, size, key):
        data = {
            'size': size,
        }
        self.event.emit('denotation-list:keypress', data)

    def init_event_listeners(self):
        def signal_handler():
            self.update_focus()
        self.modified_signal = urwid.connect_signal(self.list_walker, 'modified', signal_handler)

    def get_selected_annotation(self):
        return self.list_walker[self.focus_position].annotation

    def update_focus(self):
        if self.previous_focus_position != self.focus_position:
            if self.previous_focus_position is not None:
                self.update_focus_attr({}, position=self.previous_focus_position)
        self.update_focus_attr('reveal focus')
        self.previous_focus_position = self.focus_position

    def update_focus_attr(self, attr, position=None):
        attr = attr if isinstance(attr, dict) else {None: attr}
        if position is None:
            position = self.focus_position
        self.list_walker[position].row.set_attr_map(attr)

    def update_focus_blur(self, op):
        attr = 'reveal focus' if op == 'focus' else 'button cancel'
        self.update_focus_attr(attr)

class SelectableRow(urwid.WidgetWrap):
    """Wraps 'urwid.Columns' to make it selectable.
    """

    def __init__(self, annotation, position, widths, formatter, align="left", on_select=None, space_between=2):
        self.annotation = annotation
        self.position = position

        self._columns = urwid.Columns([
            (widths['entry'], urwid.Text(annotation['entry'].strftime(formatter.annotation), align=align)),
            (widths['description'], urwid.Text(annotation['description'], align=align)),
        ], dividechars=space_between)

        self.row = urwid.AttrMap(self._columns, '')

        # Wrap 'urwid.Columns'.
        super().__init__(self.row)

        # A hook which defines the behavior that is executed when a specified key is pressed.
        self.on_select = on_select

    def __repr__(self):
        return "{}(entry={}, description={})".format(self.__class__.__name__,
                                          self.annotation['entry'], self.annotation['description'])

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self.on_select:
            key = self.on_select(self, size, key)
        return key


class DenotationPopUpDialog(urwid.WidgetWrap):
    """A dialog for denotating tasks."""
    # TODO: Is this necessary? Copied from examples.
    signals = ['close']
    def __init__(self, task, listbox, formatter, event=None):
        self.task = task
        self.listbox = listbox
        self.formatter = formatter
        self.event = event
        self.uuid = self.task['uuid']
        denotate_button = urwid.AttrWrap(urwid.Button("Denotate"), '', 'button action')
        cancel_button = urwid.AttrWrap(urwid.Button("Cancel"), '', 'button cancel')
        # TODO: Calculate these dynamically?
        widths = {
            'entry': 10,
            'description': 32,
        }
        annotations = [SelectableRow(a, idx, widths, self.formatter) for idx, a in enumerate(self.task['annotations'])]
        self.listbox.list_walker[:] = annotations
        self.listbox.focus_position = 0
        def denotate(button):
            self._emit("close")
            data = {
                'uuid': self.uuid,
                'annotation': self.listbox.get_selected_annotation(),
            }
            self.event.emit("task:denotate", data)
        urwid.connect_signal(denotate_button.original_widget, 'click', denotate)
        urwid.connect_signal(cancel_button.original_widget, 'click',
            lambda button:self._emit("close"))
        frame = AnnotationFrame(
            urwid.Padding(self.listbox, left=1, right=1),
            header=urwid.Text("Select the annotation, then select 'Denotate'\n"),
            footer=urwid.Columns([urwid.Padding(denotate_button, left=5, right=6), urwid.Padding(cancel_button, left=6, right=5)]),
        )
        padded_frame = urwid.Padding(frame, left=1, right=1)
        box = urwid.LineBox(padded_frame, "Denotate task %s" % util.task_id_or_uuid_short(task))
        super().__init__(urwid.AttrWrap(box, 'pop_up'))

class DenotationPopupLauncher(urwid.PopUpLauncher):
    def __init__(self, original_widget, formatter, screen, event=None, request_reply=None, action_manager=None):
        self.formatter = formatter
        self.screen = screen
        self.event = event
        self.request_reply = request_reply
        self.action_manager = action_manager
        self.listbox = AnnotationListBox(urwid.SimpleFocusListWalker([]), event=self.event, request_reply=self.request_reply, action_manager=self.action_manager)
        super().__init__(original_widget)

    def set_task(self, task):
        self.task = task

    def open(self, task):
        self.set_task(task)
        self.open_pop_up()

    def create_pop_up(self):
        pop_up = DenotationPopUpDialog(self.task, self.listbox, self.formatter, event=self.event)
        urwid.connect_signal(pop_up, 'close',
            lambda button: self.close_pop_up())
        return pop_up

    def get_pop_up_parameters(self):
        screen_width, _ = self.screen.get_cols_rows()
        left = round((screen_width - OVERLAY_WIDTH) / 2)
        return {'left':left, 'top':1, 'overlay_width':OVERLAY_WIDTH, 'overlay_height':OVERLAY_HEIGHT}
