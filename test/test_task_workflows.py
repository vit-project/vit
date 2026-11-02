"""Protect persisted task changes and cancellation through VIT user actions."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from test.support import TaskEnvironment, VitHarness

pytestmark = pytest.mark.integration


class TestTaskWorkflows:
    """Change the selected task while leaving unrelated tasks untouched."""

    @pytest.mark.parametrize("key,status", [("d", "completed"), ("D", "deleted")])
    def test_confirmation_disabled(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        status: str,
    ) -> None:
        """Disabling confirmations executes the action on the selected task."""
        config = taskwarrior.vit_config.read_text(encoding="utf-8")
        taskwarrior.vit_config.write_text(
            config.replace("wait=no", "wait=no\nconfirmation=no"), encoding="utf-8"
        )
        selected = taskwarrior.add("Alpha")
        neighbor = taskwarrior.add("Beta")
        vit = make_vit()
        vit.press([key])
        assert taskwarrior.export()[selected]["status"] == status
        assert taskwarrior.export()[neighbor]["status"] == "pending"
        assert vit.focused_uuid == neighbor

    @pytest.mark.parametrize("key,status", [("d", "completed"), ("D", "deleted")])
    def test_confirm_destructive_action(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        status: str,
    ) -> None:
        """Confirmation changes the selected UUID and moves focus safely."""
        selected = taskwarrior.add("Alpha")
        neighbor = taskwarrior.add("Beta")
        before = taskwarrior.export()[neighbor]
        vit = make_vit()
        vit.press([key, "y"])
        records = taskwarrior.export()
        assert records[selected]["status"] == status
        assert records[neighbor] == before
        assert vit.displayed_uuids == [neighbor]
        assert vit.focused_uuid == neighbor

    @pytest.mark.parametrize("key", ["d", "D", "b"])
    @pytest.mark.parametrize("cancel", ["n", "esc"])
    def test_cancel_confirmation(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        cancel: str,
    ) -> None:
        """Declining or escaping a confirmation never writes task data."""
        selected = taskwarrior.add("Alpha")
        before = taskwarrior.export()
        vit = make_vit()
        vit.press([key, cancel])
        assert taskwarrior.export() == before
        assert vit.focused_uuid == selected
        assert vit.app.widget.focus_position == "body"

    def test_add_and_modify_quoted_description(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """CLI-backed edits preserve quoting, Unicode and task identity."""
        neighbor = taskwarrior.add("Neighbor")
        before = taskwarrior.export()[neighbor]
        vit = make_vit()
        vit.enter("a", '"Alpha café 漢字" project:work +review')
        records = taskwarrior.export()
        created = (records.keys() - {neighbor}).pop()
        assert records[created]["description"] == "Alpha café 漢字"
        assert records[created]["tags"] == ["review"]
        vit.app.task_list.focus_by_task_uuid(created)
        vit.enter("m", 'description:"Changed words" priority:H')
        records = taskwarrior.export()
        assert records[created]["description"] == "Changed words"
        assert records[created]["priority"] == "H"
        assert records[neighbor] == before
        assert vit.focused_uuid == created

    @pytest.mark.parametrize(
        "key,text,field,expected",
        [
            ("p", "work.child", "project", "work.child"),
            ("p", "", "project", None),
            ("T", "+new -old", "tags", ["new"]),
        ],
    )
    def test_edit_selected_field(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
        text: str,
        field: str,
        expected: str | list[str] | None,
    ) -> None:
        """Field prompts persist changes, including clearing optional values."""
        selected = taskwarrior.add("Alpha", "project:original", "+old")
        neighbor = taskwarrior.add("Beta")
        before = taskwarrior.export()[neighbor]
        vit = make_vit()
        vit.enter(key, text)
        records = taskwarrior.export()
        assert records[selected].get(field) == expected
        assert records[neighbor] == before
        assert vit.focused_uuid == selected

    def test_priority_set_and_clear(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Priority choices support both configured values and no priority."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.press(["P", "h"])
        assert taskwarrior.export()[selected]["priority"] == "H"
        vit.press(["P", "n"])
        assert "priority" not in taskwarrior.export()[selected]

    def test_start_and_stop(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """The same action starts an inactive task and stops an active task."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.press(["b", "y"])
        assert taskwarrior.export()[selected]["start"]
        vit.press(["b", "y"])
        assert "start" not in taskwarrior.export()[selected]

    def test_annotate_and_denotate(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Annotations retain literal punctuation and can be removed again."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.enter("A", 'Customer said "ship it" — café')
        annotations = taskwarrior.export()[selected]["annotations"]
        assert annotations[0]["description"] == 'Customer said "ship it" — café'
        task = vit.app.model.get_task(selected)
        assert task
        vit.app.denotate_task({"uuid": selected, "annotation": task["annotations"][0]})
        assert not taskwarrior.export()[selected].get("annotations")

    def test_wait_hides_task_from_pending_report(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Waiting uses Taskwarrior date parsing and refreshes the report."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.enter("w", "tomorrow")
        record = taskwarrior.export()[selected]
        assert record["wait"]
        assert selected in taskwarrior.command("+WAITING", "uuids")
        assert vit.displayed_uuids == []
        assert vit.focused_uuid is None

    @pytest.mark.parametrize("key", ["a", "m", "p", "T", "A", "w"])
    def test_escape_text_edit(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
    ) -> None:
        """Abandoning typed input must not create or modify any task."""
        selected = taskwarrior.add("Alpha")
        before = taskwarrior.export()
        vit = make_vit()
        vit.enter(key, "unsubmitted input", submit="esc")
        assert taskwarrior.export() == before
        assert vit.focused_uuid == selected

    def test_undo_restores_last_change(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Undo reaches the backend and restores the visible task value."""
        selected = taskwarrior.add("Alpha", "project:original")
        vit = make_vit()
        vit.enter("p", "changed")
        vit.press(["u"])
        assert taskwarrior.export()[selected]["project"] == "original"
        assert "original" in vit.render()

    def test_wait_changes_only_the_selected_recurring_instance(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Wait affects one occurrence, allowing template bookkeeping updates."""
        taskwarrior.command("add", "Recurring task", "recur:daily", "due:today")
        vit = make_vit()
        selected = vit.focused_uuid
        assert selected is not None
        before = taskwarrior.export()
        template = before[selected]["parent"]
        vit.enter("w", "tomorrow")
        after = taskwarrior.export()
        assert after[selected]["wait"]
        for snapshot in (before, after):
            snapshot[template].pop("mask", None)
            snapshot[template].pop("modified", None)
        assert after[template] == before[template]
        assert {key: value for key, value in after.items() if key != selected} == {
            key: value for key, value in before.items() if key != selected
        }
