import string
import re

class Readline(object):
    def __init__(self, edit_obj):
        self.edit_obj = edit_obj
        word_chars = string.ascii_letters + string.digits + "_"
        self._word_regex1 = re.compile(
            "([%s]+)" % "|".join(re.escape(ch) for ch in word_chars)
        )
        self._word_regex2 = re.compile(
            "([^%s]+)" % "|".join(re.escape(ch) for ch in word_chars)
        )

    def keys(self):
        return ('ctrl p', 'ctrl n', 'ctrl a', 'ctrl e', 'ctrl b', 'ctrl f',
                'ctrl h', 'ctrl d', 'ctrl t', 'ctrl u', 'ctrl k', 'meta b',
                'meta f', 'ctrl w', 'meta d')

    def keypress(self, key):
        # Move to the previous line.
        if key in ('ctrl p',):
            text = self.edit_obj.history.previous(self.edit_obj.metadata['history'])
            if text != False:
                self.edit_obj.set_edit_text(text)
            return None
        # Move to the next line.
        elif key in ('ctrl n',):
            text = self.edit_obj.history.next(self.edit_obj.metadata['history'])
            if text != False:
                self.edit_obj.set_edit_text(text)
            return None
        # Jump to the beginning of the line.
        elif key in ('ctrl a',):
            self.edit_obj.set_edit_pos(0)
            return None
        # Jump to the end of the line.
        elif key in ('ctrl e',):
            self.edit_obj.set_edit_pos(len(self.edit_obj.get_edit_text()))
            return None
        # Jump backward one character.
        elif key in ('ctrl b',):
            self.edit_obj.set_edit_pos(self.edit_obj.edit_pos - 1)
            return None
        # Jump forward one character.
        elif key in ('ctrl f',):
            self.edit_obj.set_edit_pos(self.edit_obj.edit_pos + 1)
            return None
        # Delete previous character.
        elif key in ('ctrl h',):
            if self.edit_obj.edit_pos > 0:
                self.edit_obj.set_edit_pos(self.edit_obj.edit_pos - 1)
                self.edit_obj.set_edit_text(
                    self.edit_obj.get_edit_text()[0 : self.edit_obj.edit_pos]
                    + self.edit_obj.get_edit_text()[self.edit_obj.edit_pos + 1 :])
            return None
        # Delete next character.
        elif key in ('ctrl d',):
            if self.edit_obj.edit_pos < len(self.edit_obj.get_edit_text()):
                edit_pos = self.edit_obj.edit_pos
                self.edit_obj.set_edit_text(
                    self.edit_obj.get_edit_text()[0 : self.edit_obj.edit_pos] +
                    self.edit_obj.get_edit_text()[self.edit_obj.edit_pos + 1 :])
                self.edit_obj.set_edit_pos(edit_pos)
            return None
        # Transpose characters.
        elif key in ('ctrl t',):
            # Can't transpose if there are less than 2 chars
            if len(self.edit_obj.get_edit_text()) < 2:
                return None
            self.edit_obj.set_edit_pos(max(2, self.edit_obj.edit_pos + 1))
            new_edit_pos = self.edit_obj.edit_pos

            edit_text = self.edit_obj.get_edit_text()
            self.edit_obj.set_edit_text(
                        edit_text[: new_edit_pos - 2] +
                        edit_text[new_edit_pos - 1] +
                        edit_text[new_edit_pos - 2] +
                        edit_text[new_edit_pos :])
            self.edit_obj.set_edit_pos(new_edit_pos)
            return None
        # Delete backwards to the beginning of the line.
        elif key in ('ctrl u',):
            self.edit_obj.set_edit_text(self.edit_obj.get_edit_text()[self.edit_obj.edit_pos :])
            self.edit_obj.set_edit_pos(0)
            return None
        # Delete forwards to the end of the line.
        elif key in ('ctrl k',):
            self.edit_obj.set_edit_text(self.edit_obj.get_edit_text()[: self.edit_obj.edit_pos])
            return None
        # Jump backward one word.
        elif key in ('meta b',):
            self.jump_backward_word()
            return None
        # Jump forward one word.
        elif key in ('meta f',):
            self.jump_forward_word()
            return None
        # Delete backwards to the beginning of the current word.
        elif key in ('ctrl w',):
            old_edit_pos = self.edit_obj.edit_pos
            self.jump_backward_word()
            new_edit_pos = self.edit_obj.edit_pos
            self.edit_obj.set_edit_text(self.edit_obj.edit_text[: new_edit_pos]
                + self.edit_obj.edit_text[old_edit_pos :])
            self.edit_obj.set_edit_pos(new_edit_pos)
            return None
        # Delete forwards to the end of the current word.
        elif key in ('meta d',):
            edit_pos = self.edit_obj.edit_pos
            self.jump_forward_word()
            self.edit_obj.set_edit_text(self.edit_obj.edit_text[: edit_pos]
                + self.edit_obj.edit_text[self.edit_obj.edit_pos :])
            self.edit_obj.set_edit_pos(edit_pos)
            return None

    def jump_backward_word(self):
        for match in self._word_regex1.finditer(
            self.edit_obj.edit_text[: self.edit_obj.edit_pos][::-1]
        ):
            self.edit_obj.set_edit_pos(self.edit_obj.edit_pos - match.end(1))
            return
        self.edit_obj.set_edit_pos(0)

    def jump_forward_word(self):
        for match in self._word_regex2.finditer(
            self.edit_obj.edit_text[self.edit_obj.edit_pos :]
        ):
            if match.start(1) > 0:
                self.edit_obj.set_edit_pos(self.edit_obj.edit_pos + match.start(1))
                return
        self.edit_obj.set_edit_pos(len(self.edit_obj.edit_text))

