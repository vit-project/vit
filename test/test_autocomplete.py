"""Check completion text and cursor behavior without a Taskwarrior process."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vit.autocomplete import AutoComplete
from vit.util import string_to_args


@pytest.fixture
def completion(monkeypatch: pytest.MonkeyPatch) -> tuple[AutoComplete, Mock]:
    """Supply deterministic backend candidates to the real completion engine."""
    autocomplete = AutoComplete(SimpleNamespace(taskrc_path="unused"))
    candidates = {
        "_columns": "description\nproject\npriority\n",
        "_projects": "work.alpha\nwork.beta\nHome Office\n",
        "_tags": "review\nrelease\n",
    }

    def run(arguments: list[str], capture_output: bool = False) -> tuple[int, str, str]:
        """Return the requested candidate list as Taskwarrior would."""
        assert capture_output
        return 0, candidates[arguments[-1]], ""

    monkeypatch.setattr(autocomplete.command, "run", run)
    callback = Mock()
    autocomplete.setup(callback)
    return autocomplete, callback


class TestAutocomplete:
    """Complete arguments without changing unrelated command text."""

    def test_unique_match_preserves_prefix_suffix_and_cursor(
        self,
        completion: tuple[AutoComplete, Mock],
    ) -> None:
        """Completion in the middle of a command preserves following arguments."""
        autocomplete, callback = completion
        autocomplete.activate("project:work.a +review", len("project:work.a"))
        text, cursor = callback.call_args.args
        assert string_to_args(text) == ["project:work.alpha", "+review"]
        assert text[:cursor].rstrip() == "project:work.alpha"
        assert text[cursor:].strip() == "+review"

    def test_project_with_spaces_remains_one_argument(
        self,
        completion: tuple[AutoComplete, Mock],
    ) -> None:
        """A completed project containing spaces stays quoted for submission."""
        autocomplete, callback = completion
        autocomplete.activate("project:H", len("project:H"))
        text, cursor = callback.call_args.args
        assert string_to_args(text) == ["project:Home Office"]
        assert cursor == len(text)

    def test_common_prefix_then_forward_reverse_cycle(
        self,
        completion: tuple[AutoComplete, Mock],
    ) -> None:
        """Repeated Tab cycles candidates and Shift-Tab reverses that cycle."""
        autocomplete, callback = completion
        text = "project:wo"
        autocomplete.activate(text, len(text))
        assert callback.call_args.args[0] == "project:work"
        autocomplete.activate("project:work", len("project:work"))
        first = callback.call_args.args[0]
        assert first == "project:work.alpha"
        autocomplete.activate(first, len(first))
        second = callback.call_args.args[0]
        assert second == "project:work.beta"
        autocomplete.activate(second, len(second), reverse=True)
        assert callback.call_args.args[0] == first

    @pytest.mark.parametrize("prefix", ["+", "-"])
    def test_tag_prefix_is_preserved(
        self,
        completion: tuple[AutoComplete, Mock],
        prefix: str,
    ) -> None:
        """Completion preserves the distinction between adding and removing tags."""
        autocomplete, callback = completion
        autocomplete.activate(prefix + "rev", 4)
        assert callback.call_args.args[0].strip() == prefix + "review"

    def test_no_match_preserves_input(
        self, completion: tuple[AutoComplete, Mock]
    ) -> None:
        """An unknown fragment is left intact."""
        autocomplete, callback = completion
        text = "project:unmatched"
        autocomplete.activate(text, len(text))
        assert callback.call_args.args[0] == text

    def test_backend_failure_reports_original_error(
        self,
        completion: tuple[AutoComplete, Mock],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A failed candidate lookup retains the backend diagnostic."""
        autocomplete, _ = completion
        monkeypatch.setattr(
            autocomplete.command,
            "run",
            Mock(return_value=(1, "", "database unavailable")),
        )
        with pytest.raises(RuntimeError, match="database unavailable"):
            autocomplete.refresh_type("project")
