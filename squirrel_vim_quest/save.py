"""Progress for the one player profile, stored as JSON in %APPDATA%."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("SVQ_DATA_DIR")
    if override:
        return Path(override)
    return Path(os.environ.get("APPDATA") or Path.home()) / "SquirrelVimQuest"


@dataclass
class Save:
    stars: dict[str, int] = field(default_factory=dict)  # best stars per level id
    acorns: dict[str, int] = field(default_factory=dict)  # best acorns per level id
    sound: bool = True

    @classmethod
    def load(cls) -> Save:
        path = data_dir() / "save.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        except (OSError, ValueError, TypeError):
            return cls()

    def write(self) -> None:
        folder = data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "save.json").write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def record(self, level_id: str, stars: int, acorns: int) -> None:
        self.stars[level_id] = max(stars, self.stars.get(level_id, 0))
        self.acorns[level_id] = max(acorns, self.acorns.get(level_id, 0))
        self.write()

    def stars_for(self, level_id: str) -> int:
        return self.stars.get(level_id, 0)

    def total_acorns(self) -> int:
        return sum(self.acorns.values())
