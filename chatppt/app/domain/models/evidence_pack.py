from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    source_type: Literal["official_report", "user_upload", "web_search", "knowledge_base"] = "user_upload"
    title: str
    uri: str
    reliability: float = Field(default=0.8, ge=0.0, le=1.0)


class EvidenceFact(BaseModel):
    fact_id: str = ""
    claim: str
    source: EvidenceSource


class EvidenceSuggestion(BaseModel):
    suggestion_id: str = ""
    text: str
    rationale: str = ""
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class EvidencePack(BaseModel):
    facts: list[EvidenceFact] = Field(default_factory=list)
    suggestions: list[EvidenceSuggestion] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
