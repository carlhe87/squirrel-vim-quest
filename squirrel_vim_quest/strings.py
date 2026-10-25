"""All shown and spoken text, loaded from strings/<lang>.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

_DIR = Path(__file__).parent / "strings"
_strings: dict[str, str] = {}


def load(lang: str = "en") -> None:
    _strings.clear()
    _strings.update(yaml.safe_load((_DIR / f"{lang}.yaml").read_text(encoding="utf-8")))


def t(line: str, **values: str) -> str:
    if not _strings:
        load()
    return _strings.get(line, line).format(**values)
