"""Exercise keyboard customization and search through real VIT widgets."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import Mock

import pytest

from test.support import TaskEnvironment, VitHarness

pytestmark = pytest.mark.integration


class TestKeyboardWorkflows:
    """Keep key-driven actions aligned with the displayed selection."""

    def test_user_binding_overrides_and_disables_default(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """A custom completion binding works while a disabled default does not."""
        with taskwarrior.vit_config.open("a", encoding="utf-8") as stream:
            stream.write("[keybinding]\nd={ACTION_NOOP}\nx={ACTION_TASK_DONE}\n")
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.press(["d"])
        assert vit.app.widget.focus_position == "body"
        assert taskwarrior.export()[selected]["status"] == "pending"
        vit.press(["x", "y"])
        assert taskwarrior.export()[selected]["status"] == "completed"

    def test_macro_uses_selected_task_description(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Task-variable expansion uses the current selection at execution time."""
        with taskwarrior.vit_config.open("a", encoding="utf-8") as stream:
            stream.write("[keybinding]\nx=A{TASK_DESCRIPTION}<Enter>\n")
        first = taskwarrior.add("Alpha")
        second = taskwarrior.add("Beta")
        vit = make_vit()
        vit.press(["j", "x"])
        records = taskwarrior.export()
        assert records[second]["annotations"][0]["description"] == "Beta"
        assert not records[first].get("annotations")

    def test_literal_search_next_previous_wrap_and_no_match(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Search treats punctuation literally and preserves focus on failure."""
        monkeypatch.setattr("vit.application.time.sleep", Mock())
        first = taskwarrior.add("Alpha [x]")
        second = taskwarrior.add("Beta [x]")
        taskwarrior.add("Gamma x")
        vit = make_vit()
        vit.enter("/", "[x]")
        assert vit.focused_uuid == second
        vit.press(["n"])
        assert vit.focused_uuid == first
        vit.press(["N"])
        assert vit.focused_uuid == second
        vit.enter("/", "missing")
        assert vit.focused_uuid == second
        assert "Pattern not found" in vit.message

    def test_command_history_is_separate_from_search(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """History recall restores the previous command for the current prompt."""
        taskwarrior.add("Alpha")
        vit = make_vit()
        vit.enter("A", "first annotation")
        vit.enter("/", "Alpha")
        vit.press(["A", "up"])
        assert vit.app.command_bar.get_edit_text() == "first annotation"
        vit.press(["esc"])
