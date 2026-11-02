"""Protect useful report ordering, hierarchy and terminal-width rendering."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from test.support import TaskEnvironment, VitHarness

pytestmark = pytest.mark.integration


class TestReportDisplay:
    """Assert meaningful display content without brittle screen snapshots."""

    def test_priority_and_secondary_sort_with_missing_values(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Configured priority order takes precedence over description order."""
        taskwarrior.configure("report.test.sort=priority+,description+")
        low = taskwarrior.add("Alpha", "priority:L")
        high_z = taskwarrior.add("Zulu", "priority:H")
        unset = taskwarrior.add("Unset")
        high_a = taskwarrior.add("Bravo", "priority:H")
        medium = taskwarrior.add("Medium", "priority:M")
        vit = make_vit()
        assert vit.displayed_uuids == [high_a, high_z, medium, low, unset]

    @pytest.mark.parametrize("direction", ["+", "-"])
    def test_custom_uda_order(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        direction: str,
    ) -> None:
        """String UDA sorting uses configured values instead of alphabetic order."""
        taskwarrior.configure(
            "uda.stage.type=string\nuda.stage.label=Stage\n"
            + "uda.stage.values=review,active,backlog,\n"
            + f"report.test.sort=stage{direction}\n"
            + "report.test.columns=id,description,stage"
        )
        backlog = taskwarrior.add("Backlog", "stage:backlog")
        review = taskwarrior.add("Review", "stage:review")
        active = taskwarrior.add("Active", "stage:active")
        unset = taskwarrior.add("Unset")
        vit = make_vit()
        expected = [review, active, backlog, unset]
        assert vit.displayed_uuids == (expected if direction == "+" else expected[::-1])
        assert "review" in vit.render()

    def test_string_uda_without_enumerated_values(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Free-form UDA values remain sortable, including absent values."""
        taskwarrior.configure(
            "uda.client.type=string\nuda.client.label=Client\n"
            + "report.test.columns=id,description,client\nreport.test.sort=client+"
        )
        zulu = taskwarrior.add("First", "client:Zulu")
        unset = taskwarrior.add("Second")
        alpha = taskwarrior.add("Third", "client:Alpha")
        vit = make_vit()
        assert vit.displayed_uuids == [alpha, zulu, unset]

    def test_nested_project_headings_are_not_task_targets(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Inserted parent headings render once and navigation skips them."""
        taskwarrior.configure("report.test.sort=project+,description+")
        first = taskwarrior.add("Alpha", "project:work.team.one")
        second = taskwarrior.add("Beta", "project:work.team.two")
        vit = make_vit()
        headings = [
            row.project for row in vit.app.table.rows if not hasattr(row, "uuid")
        ]
        assert headings == ["work", "work.team"]
        assert vit.focused_uuid == first
        vit.press(["j"])
        assert vit.focused_uuid == second
        vit.press(["g", "g"])
        assert vit.focused_uuid == first
        assert "↪" in vit.render()

    @pytest.mark.parametrize("size", [(40, 12), (100, 30)])
    def test_unicode_annotations_and_resize(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        size: tuple[int, int],
    ) -> None:
        """Wide and combining characters and annotations survive rendering."""
        taskwarrior.configure("report.test.columns=id,description")
        taskwarrior.add("漢字 cafe\u0301")
        vit = make_vit()
        vit.enter("A", "Important annotation")
        text = vit.render(size)
        assert "漢字 cafe\u0301" in text
        assert "Important annotation" in text
        assert "漢字 cafe\u0301" in vit.render((80, 24))

    def test_dependency_indicator_clears_when_blocker_completes(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """The dependency indicator reflects current blocking tasks."""
        taskwarrior.configure(
            "report.test.columns=id,description,depends.indicator\n"
            + "report.test.labels=ID,Description,Blocked\ndependency.indicator=BLOCKED"
        )
        blocker = taskwarrior.add("Alpha prerequisite")
        taskwarrior.add("Beta blocked", f"depends:{blocker}")
        vit = make_vit()
        assert "BLOCKED" in vit.render()
        vit.press(["d", "y"])
        assert "BLOCKED" not in vit.render()
