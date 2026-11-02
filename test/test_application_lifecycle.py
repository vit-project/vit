"""Verify the CLI starts the explicitly separated application lifecycle."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from vit.command_line import main


class TestApplicationLifecycle:
    """Keep the installed command connected to the interactive application."""

    def test_cli_runs_application(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Command-line arguments reach an application whose run method is invoked."""
        options = object()
        filters = ["next", "+work"]
        application = Mock()
        monkeypatch.setattr(
            "vit.command_line.parse_options", Mock(return_value=(options, filters))
        )
        monkeypatch.setattr("vit.command_line.Application", application)
        main()
        application.assert_called_once_with(options, filters)
        application.return_value.run.assert_called_once_with()
