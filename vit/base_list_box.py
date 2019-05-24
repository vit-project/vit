import re

import urwid

BRACKETS_REGEX = re.compile("[<>]")

class BaseListBox(urwid.ListBox):
    """Maps task list shortcuts to default ListBox class.
    """

    def __init__(self, body, event=None, request_reply=None, action_manager=None):
        self.previous_focus_position = None
        self.list_walker = body
        self.event = event
        self.request_reply = request_reply
        self.action_manager = action_manager
        self.key_cache = self.request_reply.request('application:key_cache')
        self.register_managed_actions()
        return super().__init__(body)

    def get_top_middle_bottom_rows(self, size):
        #try:
            if len(self.list_walker) == 0:
                return None, None, None
            ((_, focused, _, _, _), (_, top_list), (_, bottom_list)) = self.calculate_visible(size)
            top = top_list[len(top_list) - 1][0] if len(top_list) > 0 else None
            bottom = bottom_list[len(bottom_list) - 1][0] if len(bottom_list) > 0 else None
            top_list_reversed = []
            # Neither top_list.reverse() nor reversed(top_list) works here, WTF?
            while True:
                if len(top_list) > 0:
                    row = top_list.pop()
                    top_list_reversed.append(row)
                else:
                    break
            assembled_list = top_list_reversed + [(focused, )] + (bottom_list if bottom else [])
            middle_list_position = (len(assembled_list) // 2) + 1
            middle_list = assembled_list[:middle_list_position] if len(assembled_list) > 1 else assembled_list
            middle = middle_list.pop()[0]
            return (top or focused), middle, (bottom or focused)
        #except:
        #    # TODO: Log this?
        #    return None, None, None

    def register_managed_actions(self):
        self.action_manager_registrar = self.action_manager.get_registrar()
        self.action_manager_registrar.register('LIST_UP', self.keypress_up)
        self.action_manager_registrar.register('LIST_DOWN', self.keypress_down)
        self.action_manager_registrar.register('LIST_PAGE_UP', self.keypress_page_up)
        self.action_manager_registrar.register('LIST_PAGE_DOWN', self.keypress_page_down)
        self.action_manager_registrar.register('LIST_HOME', self.keypress_home)
        self.action_manager_registrar.register('LIST_END', self.keypress_end)
        self.action_manager_registrar.register('LIST_SCREEN_TOP', self.keypress_screen_top)
        self.action_manager_registrar.register('LIST_SCREEN_MIDDLE', self.keypress_screen_middle)
        self.action_manager_registrar.register('LIST_SCREEN_BOTTOM', self.keypress_screen_bottom)
        self.action_manager_registrar.register('LIST_FOCUS_VALIGN_CENTER', self.keypress_focus_valign_center)

    # NOTE: The non-standard key presses work around infinite recursion while
    #       allowing the up, down, page up, and page down keys to be controlled
    #       from the keybinding file.
    def keypress_up(self, size):
        self.keypress(size, '<Up>')

    def keypress_down(self, size):
        self.keypress(size, '<Down>')

    def keypress_page_up(self, size):
        self.keypress(size, '<Page Up>')

    def keypress_page_down(self, size):
        self.keypress(size, '<Page Down>')

    def keypress_home(self, size):
        self.set_focus(0)

    def keypress_end(self, size):
        self.set_focus(len(self.body) - 1)
        self.set_focus_valign('bottom')

    def keypress_screen_top(self, size):
        top, _, _ = self.get_top_middle_bottom_rows(size)
        if top:
            self.set_focus(top.position)

    def keypress_screen_middle(self, size):
        _, middle, _ = self.get_top_middle_bottom_rows(size)
        if middle:
            self.set_focus(middle.position)

    def keypress_screen_bottom(self, size):
        _, _, bottom = self.get_top_middle_bottom_rows(size)
        if bottom:
            self.set_focus(bottom.position)

    def keypress_focus_valign_center(self, size):
        self.set_focus(self.focus_position)
        self.set_focus_valign('middle')

    def transform_special_keys(self, key):
        # NOTE: These are special key presses passed to allow navigation
        #       keys to be managed via keybinding configuration. They are
        #       converted back to standard key presses here.
        if key in ['<Up>', '<Down>', '<Page Up>', '<Page Down>']:
            key = re.sub(BRACKETS_REGEX, '', key).lower()
        return key

    def list_action_executed(self, size, key):
        pass

    def eat_other_keybindings(self):
        return False

    def keypress(self, size, key):
        keys = self.key_cache.get(key)
        if self.action_manager_registrar.execute_handler(keys, size):
            self.list_action_executed(size, key)
            return None
        if self.eat_other_keybindings() and self.key_cache.is_keybinding(keys):
            return None
        key = self.transform_special_keys(key)
        return super().keypress(size, key)


