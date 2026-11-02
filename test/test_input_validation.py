"""Protect command-bar input from silent loss on malformed quoting."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from test.support import TaskEnvironment, VitHarness

pytestmark = pytest.mark.integration


class TestInputValidation:
    """Exercise validation and recovery through real widgets and task storage."""

    @pytest.mark.parametrize("key", ["A", "a", "m", "f"])
    @pytest.mark.parametrize(
        "text,error",
        [
            ("foo'bar", "No closing quotation"),
            ('foo"bar', "No closing quotation"),
            ('"unending', "No closing quotation"),
            ("'", "No closing quotation"),
            ('"', "No closing quotation"),
            ("trailing\\", "No escaped character"),
            ("  foo'bar  ", "No closing quotation"),
        ],
    )
    def test_invalid_input_remains_editable(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        text: str,
        error: str,
    ) -> None:
        """Repeated submission preserves input, cursor, selection and task data."""
        selected = taskwarrior.add("Alpha")
        taskwarrior.add("Beta")
        before = taskwarrior.export()
        vit = make_vit()
        vit.press([key])
        command_bar = vit.app.command_bar
        metadata = command_bar.get_metadata()
        assert metadata is not None
        caption = str(command_bar.caption)
        command_bar.set_edit_text(text)
        command_bar.set_edit_pos(0)
        for _ in range(2):
            vit.press(["enter"])
            assert command_bar.get_edit_text() == text
            assert command_bar.edit_pos == 0
            assert command_bar.get_metadata() == metadata
            assert str(command_bar.caption).count("Invalid input:") == 1
            assert caption in str(command_bar.caption)
            assert error in vit.render()
            assert vit.app.widget.focus_position == "footer"
            assert vit.focused_uuid == selected
            assert not command_bar.history.exists(metadata["history"])
            assert taskwarrior.export() == before

    @pytest.mark.parametrize("key", ["A", "a"])
    @pytest.mark.parametrize(
        "invalid,correction,submitted,description",
        [
            (
                'Customer said "ship it',
                '"',
                'Customer said "ship it"',
                "Customer said ship it",
            ),
            ("trailing\\", "backspace", "trailing", "trailing"),
        ],
    )
    def test_correct_and_resubmit(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        invalid: str,
        correction: str,
        submitted: str,
        description: str,
    ) -> None:
        """Editing the retained text clears the error and saves exactly once."""
        selected = taskwarrior.add("Existing task")
        before = taskwarrior.export()[selected]
        vit = make_vit()
        vit.enter(key, invalid)
        command_bar = vit.app.command_bar
        assert "Invalid input:" in str(command_bar.caption)
        vit.press([correction])
        assert "Invalid input:" not in str(command_bar.caption)
        assert command_bar.get_edit_text() == submitted
        vit.press(["enter"])
        records = taskwarrior.export()
        if key == "A":
            assert len(records) == 1
            assert [
                annotation["description"]
                for annotation in records[selected]["annotations"]
            ] == [submitted]
        else:
            assert records[selected] == before
            created = records.keys() - {selected}
            assert len(created) == 1
            assert records[created.pop()]["description"] == description
        assert vit.app.widget.focus_position == "body"
        vit.press([key, "up"])
        assert command_bar.get_edit_text() == submitted
        vit.press(["up"])
        assert command_bar.get_edit_text() == submitted

    @pytest.mark.parametrize("key", ["A", "a"])
    def test_cancel_invalid_input(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
    ) -> None:
        """Escape cancels an invalid submission and the next prompt is clean."""
        selected = taskwarrior.add("Existing task")
        before = taskwarrior.export()
        vit = make_vit()
        vit.enter(key, "foo'bar")
        vit.press(["esc"])
        assert taskwarrior.export() == before
        assert vit.focused_uuid == selected
        assert vit.app.widget.focus_position == "body"
        vit.press([key, "up"])
        assert vit.app.command_bar.get_edit_text() == ""
        assert "Invalid input:" not in str(vit.app.command_bar.caption)
        vit.press(["enter"])
        assert vit.app.widget.focus_position == "body"
        assert taskwarrior.export() == before
