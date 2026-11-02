"""Verify backend failures preserve data, diagnostics and terminal control."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vit import env
from vit.process import Command
from test.support import TaskEnvironment, VitHarness


@pytest.mark.integration
class TestApplicationFailures:
    """Keep a failed edit distinguishable from a successful one."""

    def test_failed_modify_preserves_tasks_and_restores_loop(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A rejected command reports its diagnostic and resumes the UI."""
        selected = taskwarrior.add("Alpha")
        before = taskwarrior.export()
        vit = make_vit()
        monkeypatch.setattr(
            vit.app.command, "result", Mock(return_value=(1, "Permission denied"))
        )
        vit.enter("m", "description:Changed")
        assert taskwarrior.export() == before
        assert "Permission denied" in vit.message
        assert "modified" not in vit.message
        assert vit.focused_uuid == selected
        vit.loop.stop.assert_called_once()
        vit.loop.start.assert_called_once()

    def test_exception_after_suspending_ui_restores_loop(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Even an unexpected command failure must restore terminal ownership."""
        taskwarrior.add("Alpha")
        vit = make_vit()
        monkeypatch.setattr(
            vit.app.command, "result", Mock(side_effect=RuntimeError("lost terminal"))
        )
        with pytest.raises(RuntimeError, match="lost terminal"):
            vit.app.execute_command(["task", "sync"])
        vit.loop.stop.assert_called_once()
        vit.loop.start.assert_called_once()

    def test_task_completed_externally_while_confirmation_is_open(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """A stale task selection cannot complete its renumbered neighbor."""
        selected = taskwarrior.add("Alpha")
        neighbor = taskwarrior.add("Beta")
        vit = make_vit()
        vit.press(["d"])
        taskwarrior.command(selected, "done")
        before = taskwarrior.export()
        vit.press(["y"])
        assert taskwarrior.export() == before
        assert taskwarrior.export()[neighbor]["status"] == "pending"
        assert "Error:" in vit.message

    def test_invalid_filter_can_be_corrected(
        self,
        taskwarrior: TaskEnvironment,
        make_vit: Callable[..., VitHarness],
    ) -> None:
        """A malformed expression reports an error and permits recovery."""
        selected = taskwarrior.add("Alpha")
        vit = make_vit()
        vit.enter("f", "(")
        assert "parenthes" in vit.message.lower()
        assert vit.app.widget.focus_position == "body"
        vit.enter("f", "")
        assert vit.displayed_uuids == [selected]


class TestCommandBoundary:
    """Check the subprocess contract without contacting external services."""

    def test_argument_and_environment_preservation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Arguments remain literal and per-command environment overrides expire."""
        monkeypatch.setattr(env, "user", {"VIT_TEST_VALUE": "original"})
        command = Command(SimpleNamespace(taskrc_path=str(tmp_path / "taskrc")))
        script = (
            "import json, os, sys; "
            "print(json.dumps([sys.argv[1:], os.environ['TASKRC'], os.environ['VIT_TEST_VALUE']]))"
        )
        literal = 'two words; $(echo wrong) "quoted"'
        args = [sys.executable, "-c", script, literal]
        code, stdout, error = command.run(
            args, capture_output=True, custom_env={"VIT_TEST_VALUE": "override"}
        )
        assert code == 0, error
        assert json.loads(stdout) == [[literal], str(tmp_path / "taskrc"), "override"]
        code, stdout, error = command.run(args, capture_output=True)
        assert code == 0, error
        assert json.loads(stdout)[2] == "original"

    def test_missing_executable_is_reported(self, tmp_path: Path) -> None:
        """Failure to start a process becomes a useful nonzero command result."""
        command = Command(SimpleNamespace(taskrc_path=str(tmp_path / "taskrc")))
        code, _, error = command.run(
            [str(tmp_path / "missing-command")], capture_output=True
        )
        assert code != 0
        assert "missing-command" in error
