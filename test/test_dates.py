"""Check task state and date formatting at fixed, timezone-aware boundaries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vit.formatter_base import FormatterBase
from vit.formatter.due import Due
from vit.formatter.due_relative import DueRelative


@pytest.fixture
def formatter(monkeypatch: pytest.MonkeyPatch) -> FormatterBase:
    """Build a formatter with small configuration doubles and a fixed clock."""
    task_config = Mock()
    values: dict[str, str | dict[str, str]] = {
        "dateformat": {"default": "%Y-%m-%d"},
        "dateformat.report": "%Y-%m-%d",
        "dateformat.annotation": "%Y-%m-%d",
        "due": "7",
    }

    def subtree(name: str, walk_subtree: bool = True) -> str | dict[str, str]:
        """Provide the few Taskwarrior settings used by date formatters."""
        return values.get(name, {}) if walk_subtree else {}

    def translate(value: str) -> str:
        """The test configuration already uses strftime date markers."""
        return value

    def color(state: str | None) -> str | None:
        """Expose the chosen due state in rendered markup."""
        return state

    task_config.subtree.side_effect = subtree
    task_config.translate_date_markers.side_effect = translate
    config = Mock()
    config.get.return_value = "[NONE]"
    colorizer = Mock()
    colorizer.due.side_effect = color
    result = FormatterBase(Mock(), config, task_config, SimpleNamespace(), colorizer)
    now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc).astimezone()
    clock = Mock(wraps=datetime)
    clock.now.return_value = now
    monkeypatch.setattr("vit.formatter_base.datetime", clock)
    monkeypatch.setattr("vit.formatter.datetime", clock)
    result.recalculate_due_datetimes()
    return result


class TestTaskDates:
    """Preserve urgency cues that affect what a user chooses to work on."""

    @pytest.mark.parametrize(
        "boundary,offset,state",
        [
            ("now", -1, "overdue"),
            ("now", 0, "due.today"),
            ("end_of_day", 0, "due.today"),
            ("end_of_day", 1, "due"),
            ("due_soon", -1, "due"),
            ("due_soon", 0, None),
        ],
    )
    def test_due_boundaries(
        self,
        formatter: FormatterBase,
        boundary: str,
        offset: int,
        state: str | None,
    ) -> None:
        """Exact cutoff times select the correct due color state."""
        due = getattr(formatter, boundary) + timedelta(seconds=offset)
        column = Due("due", {}, formatter, [])
        _, markup = column.format(due, {"status": "pending"})
        assert markup == (state, due.strftime("%Y-%m-%d"))

    @pytest.mark.parametrize("status", ["completed", "deleted"])
    def test_closed_tasks_are_not_overdue(
        self, formatter: FormatterBase, status: str
    ) -> None:
        """Past dates on closed tasks must not appear actionable."""
        due = formatter.now - timedelta(days=2)
        assert formatter.get_due_state(due, {"status": status}) is None

    def test_same_instant_in_another_timezone(self, formatter: FormatterBase) -> None:
        """Due comparisons use instants rather than naive wall-clock values."""
        due = formatter.now.astimezone(timezone(timedelta(hours=9)))
        assert formatter.get_due_state(due, {"status": "pending"}) == "due.today"

    def test_relative_dates_and_missing_due(self, formatter: FormatterBase) -> None:
        """Relative dates preserve past/future direction and allow no due date."""
        column = DueRelative("due", {}, formatter, [])
        task = {"status": "pending"}
        assert column.format(None, task) == (0, "")
        assert column.format(formatter.now - timedelta(days=2), task)[1][1] == "-2d"
        assert column.format(formatter.now + timedelta(days=2), task)[1][1] == "2d"
