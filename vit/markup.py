from __future__ import annotations

from dataclasses import dataclass

from urwid.util import calc_width


@dataclass(frozen=True)
class RawText:
    data: bytes


def markup_contains_raw(markup) -> bool:
    if isinstance(markup, RawText):
        return True
    if isinstance(markup, list):
        return any(markup_contains_raw(item) for item in markup)
    if isinstance(markup, tuple):
        _, inner = markup
        return markup_contains_raw(inner)
    return False


def markup_to_bytes(markup, encoding: str = "utf-8"):
    if isinstance(markup, RawText):
        return markup.data
    if isinstance(markup, bytes):
        return markup
    if isinstance(markup, str):
        return markup.encode(encoding)
    if isinstance(markup, list):
        return [markup_to_bytes(item, encoding=encoding) for item in markup]
    if isinstance(markup, tuple):
        attr, inner = markup
        return (attr, markup_to_bytes(inner, encoding=encoding))
    return markup


def normalize_markup(markup, encoding: str = "utf-8"):
    if markup_contains_raw(markup):
        return markup_to_bytes(markup, encoding=encoding)
    return markup


def markup_display_width(markup) -> int:
    if markup is None:
        return 0
    if isinstance(markup, RawText):
        return 0
    if isinstance(markup, list):
        return sum(markup_display_width(item) for item in markup)
    if isinstance(markup, tuple):
        _, inner = markup
        return markup_display_width(inner)
    if isinstance(markup, (str, bytes)):
        return calc_width(markup, 0, len(markup))
    return 0


def markup_to_str(markup, encoding: str = "utf-8") -> str:
    if markup is None:
        return ""
    if isinstance(markup, RawText):
        return ""
    if isinstance(markup, bytes):
        return markup.decode(encoding, errors="ignore")
    if isinstance(markup, str):
        return markup
    if isinstance(markup, list):
        return "".join(markup_to_str(item, encoding=encoding) for item in markup)
    if isinstance(markup, tuple):
        _, inner = markup
        return markup_to_str(inner, encoding=encoding)
    return ""
