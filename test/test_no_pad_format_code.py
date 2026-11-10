"""The strftime no-pad probe must survive platforms where unknown format
codes raise instead of passing through.

On Windows (MSVCRT), ``datetime.strftime('%-d')`` raises ``ValueError``,
which used to crash the import of ``vit.config_parser`` — and with it the
whole application. The probe now guards each code, resolving to ``'#'``
there and ``'-'`` on POSIX.
"""

from __future__ import annotations

import datetime

from vit import config_parser


def test_no_pad_format_code_is_supported() -> None:
    assert config_parser.NO_PAD_FORMAT_CODE in ('-', '#', '')


def test_date_format_mapping_codes_render() -> None:
    probe = datetime.datetime(2024, 1, 2, 3, 4, 5)
    for fmt in config_parser.DATE_FORMAT_MAPPING.values():
        assert probe.strftime(fmt)
