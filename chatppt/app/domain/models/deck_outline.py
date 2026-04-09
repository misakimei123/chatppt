from __future__ import annotations

from pydantic import BaseModel, Field


class DeckSection(BaseModel):
    section_id: str
    title: str
    purpose: str
    evidence_refs: list[str] = Field(default_factory=list)


class DeckOutline(BaseModel):
    deck_objective: str
    narrative_arc: str
    estimated_slide_count: int = Field(ge=1)
    sections: list[DeckSection] = Field(default_factory=list)
