"""Check report membership and selection against real Taskwarrior state."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from test.support import TaskEnvironment, VitHarness

pytestmark = pytest.mark.integration


class TestReportFilters:
    """Combine independent filter sources without widening the report."""

    def test_context_report_and_extra_filters(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """OR groups remain intersected with both context and user filters."""
        expected = taskwarrior.add("Alpha", "project:work", "+red", "priority:H")
        taskwarrior.add("Beta", "project:work", "+blue", "priority:L")
        taskwarrior.add("Gamma", "project:home", "+red", "priority:H")
        taskwarrior.add("Delta", "project:work", "+green", "priority:H")
        taskwarrior.configure(
            "context.work.read=project:work\ncontext=work\n"
            + "report.test.filter=status:pending and (+red or +blue)"
        )
        vit = make_vit(["test", "priority:H"])
        assert vit.displayed_uuids == [expected]
        assert "Context: work" in vit.render()

    def test_report_can_disable_context(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """A report with context=0 includes tasks outside the active context."""
        work = taskwarrior.add("Alpha", "project:work")
        home = taskwarrior.add("Beta", "project:home")
        taskwarrior.configure(
            "context.work.read=project:work\ncontext=work\nreport.test.context=0"
        )
        vit = make_vit()
        assert vit.displayed_uuids == [work, home]

    @pytest.mark.parametrize("source", ["report", "context", "extra"])
    def test_quoted_filter_value(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        source: str,
    ) -> None:
        """A quoted phrase remains one filter value through parsing and export."""
        expected = taskwarrior.add("Alpha two words together")
        taskwarrior.add("Beta two separate words")
        if source == "report":
            taskwarrior.configure(
                'report.test.filter=status:pending description.contains:"two words"'
            )
        elif source == "context":
            taskwarrior.configure(
                'context.phrase.read=description.contains:"two words"\ncontext=phrase'
            )
        vit = make_vit()
        if source == "extra":
            vit.enter("f", 'description.contains:"two words"')
        assert vit.displayed_uuids == [expected]

    def test_switch_context_and_report(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Context switching and named reports update membership and status."""
        work = taskwarrior.add("Alpha", "project:work")
        home = taskwarrior.add("Beta", "project:home")
        taskwarrior.configure(
            "context.work.read=project:work\n"
            + "report.home.columns=id,description\nreport.home.sort=description+\n"
            + "report.home.filter=project:home\nreport.home.context=0"
        )
        vit = make_vit()
        vit.enter("c", "work")
        assert vit.displayed_uuids == [work]
        vit.enter(":", "home")
        assert vit.displayed_uuids == [home]
        assert vit.app.report == "home"
        vit.enter("c", "none")
        vit.enter(":", "test")
        assert vit.displayed_uuids == [work, home]

    def test_empty_filter_results_and_recovery(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Empty reports render and accept a new filter without a stale task."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        before = taskwarrior.export()
        vit.enter("f", "+nonexistent")
        assert vit.displayed_uuids == []
        assert vit.focused_uuid is None
        vit.press(["d", "D", "b"])
        assert taskwarrior.export() == before
        vit.enter("f", "")
        assert vit.displayed_uuids == [selected]


class TestSelection:
    """Keep task identity stable across redraws and lazy row loading."""

    @pytest.mark.parametrize("key", ["d", "D"])
    def test_remove_last_task(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        key: str,
    ) -> None:
        """Removing the final task leaves a usable empty view."""
        taskwarrior.add("Only task")
        vit = make_vit()
        vit.press([key, "y"])
        assert vit.displayed_uuids == []
        assert vit.focused_uuid is None
        assert "0 tasks shown" in vit.render()
        vit.enter("a", "Replacement task")
        assert len(vit.displayed_uuids) == 1
        assert vit.focused_uuid == vit.displayed_uuids[0]

    def test_refresh_after_external_change(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Refresh reconciles externally completed and newly added tasks."""
        old = taskwarrior.add("Alpha")
        neighbor = taskwarrior.add("Beta")
        vit = make_vit()
        taskwarrior.command(old, "done")
        new = taskwarrior.add("Gamma")
        vit.press(["ctrl l"])
        assert vit.displayed_uuids == [neighbor, new]
        assert vit.focused_uuid == neighbor
        vit.press(["d", "y"])
        assert taskwarrior.export()[neighbor]["status"] == "completed"
        assert taskwarrior.export()[new]["status"] == "pending"

    def test_focus_beyond_first_batch_and_return_home(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """Navigation and UUID lookup reach tasks not yet loaded as widgets."""
        uuids = [taskwarrior.add(f"Task {number:02}") for number in range(35)]
        vit = make_vit()
        assert len(vit.app.table.list_walker) < len(uuids)
        vit.app.task_list.focus_by_task_uuid(uuids[-1])
        assert vit.focused_uuid == uuids[-1]
        vit.press(["g", "g"])
        assert vit.focused_uuid == uuids[0]
        vit.press(["G"])
        assert vit.focused_uuid == uuids[-1]
        vit.press(["d", "y"])
        assert vit.focused_uuid == uuids[-2]

    def test_edit_keeps_selected_uuid_after_sort_changes(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """A task moving to a different row remains selected by identity."""
        selected = taskwarrior.add("Alpha")
        neighbor = taskwarrior.add("Beta")
        vit = make_vit()
        vit.enter("m", "description:Zulu")
        assert vit.displayed_uuids == [neighbor, selected]
        assert vit.focused_uuid == selected
