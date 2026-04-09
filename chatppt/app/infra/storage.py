from __future__ import annotations

import json
from pathlib import Path


class ArtifactStorage:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
