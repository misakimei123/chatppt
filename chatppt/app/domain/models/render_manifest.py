from __future__ import annotations

from pydantic import BaseModel, Field


class LayoutSelection(BaseModel):
    layout_name: str
    confidence: float


class RenderedSlide(BaseModel):
    slide_id: str
    layout: LayoutSelection
    placeholder_map: dict[str, str] = Field(default_factory=dict)
    placeholder_dimensions: dict[str, dict[str, float]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class RenderManifest(BaseModel):
    template_id: str = "default"
    slides: list[RenderedSlide] = Field(default_factory=list)
