"""Protect rendering of inactive footer containers and their activation."""

from __future__ import annotations

import pytest
import urwid

from vit.multi_widget import MultiWidget


class TestMultiWidget:
    """Exercise empty containers through the real Urwid rendering path."""

    @pytest.mark.parametrize("registered", [False, True])
    def test_inactive_widget_renders_zero_rows(self, registered: bool) -> None:
        """Registered children stay hidden until explicitly selected."""
        widget = MultiWidget()
        if registered:
            widget.add_widget("message", urwid.Text("Ready"))

        canvas = widget.render((40,))

        assert canvas.cols() == 40
        assert canvas.rows() == widget.rows((40,)) == 0
        assert widget.keypress((40,), "a") == "a"

    def test_activation_replaces_cached_empty_canvas(self) -> None:
        """Showing a child invalidates an earlier empty render."""
        widget = MultiWidget()
        widget.add_widget("message", urwid.Text("Ready"))
        assert widget.render((40,)).rows() == 0

        widget.show_widget("message")
        canvas = widget.render((40,))

        assert canvas.rows() == widget.rows((40,)) == 1
        assert b"Ready" in b"".join(canvas.text)

    def test_frame_with_inactive_footer(self) -> None:
        """An inactive footer leaves the entire frame available to its body."""
        frame = urwid.Frame(urwid.SolidFill("x"), footer=MultiWidget())

        canvas = frame.render((40, 12), focus=True)

        assert canvas.cols() == 40
        assert canvas.rows() == 12
        assert list(canvas.text) == [b"x" * 40] * 12
