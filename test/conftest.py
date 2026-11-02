"""Fixtures that isolate both Taskwarrior state and terminal interactions."""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import shutil
from unittest.mock import MagicMock, Mock

import pytest

from vit import env
from vit.application import Application
from test.support import TaskEnvironment, VitHarness


@pytest.fixture
def taskwarrior(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TaskEnvironment:
    """Provide private configuration and storage for every backend test."""
    executable = shutil.which("task")
    if executable is None:
        pytest.skip("Taskwarrior is required for integration tests")
    environment = TaskEnvironment(tmp_path, executable)
    overrides = {
        "TASKRC": str(environment.taskrc),
        "TASKDATA": str(environment.data),
        "VIT_DIR": str(environment.config_dir),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
        "TZ": "UTC",
    }
    for key in list(os.environ):
        if key.startswith("TASK"):
            monkeypatch.delenv(key)
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(env, "user", os.environ.copy())
    return environment


@pytest.fixture
def make_vit(
    taskwarrior: TaskEnvironment,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> Callable[..., VitHarness]:
    """Construct the real application without a terminal, signals or PID file."""
    request.node.user_properties.append(("taskrc", str(taskwarrior.taskrc)))
    loop = MagicMock()
    loop.screen.get_cols_rows.return_value = (100, 30)
    monkeypatch.setattr("vit.application.urwid.MainLoop", Mock(return_value=loop))
    monkeypatch.setattr("vit.process.clear_screen", Mock())
    monkeypatch.setattr("builtins.input", Mock(return_value=""))

    def create(filters: list[str] | None = None) -> VitHarness:
        """Load the current test configuration and task database."""
        app = Application(None, filters or [])
        assert not loop.run.called
        return VitHarness(app, loop)

    return create
