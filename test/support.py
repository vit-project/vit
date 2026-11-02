"""Isolated Taskwarrior storage and a terminal-free VIT workflow driver."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any
from unittest.mock import MagicMock

from vit.application import Application


class TaskEnvironment:
    """Run real Taskwarrior commands against a test-owned configuration."""

    def __init__(self, root: Path, executable: str) -> None:
        self.executable: str = executable
        self.taskrc: Path = root / "taskrc"
        self.data: Path = root / "tasks"
        self.config_dir: Path = root / "vit"
        self.data.mkdir()
        self.config_dir.mkdir()
        self.taskrc.write_text(
            "\n".join(
                [
                    f"data.location={self.data}",
                    "confirmation=no",
                    "hooks=off",
                    "news.version=99.0.0",
                    "report.test.columns=id,description,project,priority",
                    "report.test.labels=ID,Description,Project,Priority",
                    "report.test.sort=description+",
                    "report.test.filter=status:pending -WAITING",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.vit_config: Path = self.config_dir / "config.ini"
        self.vit_config.write_text(
            "\n".join(
                [
                    "[vit]",
                    "flash_focus_repeat_times=0",
                    "wait=no",
                    "[report]",
                    "default_report=test",
                    "default_filter_only_report=test",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def configure(self, settings: str) -> None:
        """Append Taskwarrior settings before constructing the application."""
        with self.taskrc.open("a", encoding="utf-8") as stream:
            stream.write(settings + "\n")

    def command(self, *arguments: str) -> str:
        """Execute a command, failing promptly with its diagnostic output."""
        result = subprocess.run(
            [self.executable, *arguments],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def export(self) -> dict[str, dict[str, Any]]:
        """Read saved values, excluding computed IDs and time-sensitive urgency."""
        records = json.loads(self.command("rc.context=", "rc.json.array=on", "export"))
        for record in records:
            record.pop("id", None)
            record.pop("urgency", None)
        return {record["uuid"]: record for record in records}

    def add(self, description: str, *attributes: str) -> str:
        """Create a task and return its stable UUID."""
        before = self.export()
        self.command("add", description, *attributes)
        created = self.export().keys() - before.keys()
        assert len(created) == 1
        return created.pop()


class VitHarness:
    """Drive actual VIT widgets while replacing only terminal lifecycle I/O."""

    def __init__(self, app: Application, loop: MagicMock) -> None:
        self.app: Application = app
        self.loop: MagicMock = loop
        self.size: tuple[int, int] = (100, 30)
        self.loop.process_input.side_effect = self.press

    @property
    def focused_uuid(self) -> str | None:
        """Return the identity of the currently selected task, if any."""
        focus = self.app.task_list.focus
        return getattr(focus, "uuid", None)

    @property
    def displayed_uuids(self) -> list[str]:
        """Return all task rows in display order, excluding project headings."""
        return [row.uuid for row in self.app.table.rows if hasattr(row, "uuid")]

    @property
    def message(self) -> str:
        """Read the message visible to the user."""
        text = self.app.message_bar.get_text()[0]
        return text.decode("utf-8") if isinstance(text, bytes) else text

    def render(self, size: tuple[int, int] | None = None) -> str:
        """Render real Urwid widgets and return their visible text."""
        if size is not None:
            self.size = size
        canvas = self.app.widget.render(self.size, focus=True)
        assert canvas.cols() == self.size[0]
        assert canvas.rows() == self.size[1]
        return "\n".join(line.decode("utf-8") for line in canvas.text)

    def press(self, keys: list[str]) -> None:
        """Dispatch keys through the same widget and fallback path as Urwid."""
        for key in keys:
            self.render()
            unhandled = self.app.widget.keypress(self.size, key)
            if unhandled is not None:
                self.app.key_pressed(unhandled)

    def enter(self, action_key: str, text: str, submit: str = "enter") -> None:
        """Open a command prompt and submit or cancel its text."""
        self.press([action_key])
        assert self.app.widget.focus_position == "footer"
        self.app.command_bar.set_edit_text(text)
        self.press([submit])
