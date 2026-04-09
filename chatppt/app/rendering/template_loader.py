from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class TemplateLayout(BaseModel):
    layout_name: str
    supported_purposes: list[str] = Field(default_factory=list)
    slot_kinds: list[str] = Field(default_factory=list)
    structure: str = "single-col"
    placeholder_dimensions: dict[str, dict[str, float]] = Field(default_factory=dict)


class TemplateMeta(BaseModel):
    template_id: str
    display_name: str
    layouts: list[TemplateLayout] = Field(default_factory=list)
    brand_rules: dict[str, list[str]] = Field(default_factory=dict)
    root_path: Path


class TemplateLoader:
    def load(self, template_root: Path) -> TemplateMeta:
        template_root = Path(template_root)
        meta = json.loads((template_root / "meta.json").read_text(encoding="utf-8"))
        brand_rules = json.loads((template_root / "brand_rules.json").read_text(encoding="utf-8"))
        return TemplateMeta(
            template_id=meta["template_id"],
            display_name=meta["display_name"],
            layouts=[TemplateLayout.model_validate(layout) for layout in meta["layouts"]],
            brand_rules=brand_rules,
            root_path=template_root,
        )
