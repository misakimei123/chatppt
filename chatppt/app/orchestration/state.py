from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_serializer

from chatppt.app.domain.models.deck_ir import DeckIR
from chatppt.app.domain.models.deck_outline import DeckOutline
from chatppt.app.domain.models.editable_deck_state import EditableDeckState
from chatppt.app.domain.models.evidence_pack import EvidencePack
from chatppt.app.domain.models.render_manifest import RenderManifest


class ValidationIssue(BaseModel):
    code: str
    message: str
    slide_id: str
    severity: str = "error"


class ValidationReport(BaseModel):
    passed: bool = True
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


class SemanticFinding(BaseModel):
    code: str
    message: str
    slide_id: str
    severity: str = "warning"


class GenerationArtifacts(BaseModel):
    deck: DeckIR
    outline: DeckOutline
    evidence_pack: EvidencePack
    manifest: RenderManifest
    validation_report: ValidationReport
    editable_deck_state: EditableDeckState
    semantic_findings: list[SemanticFinding] = Field(default_factory=list)
    pptx_path: Path

    @field_serializer("pptx_path")
    def serialize_pptx_path(self, value: Path) -> str:
        return str(value)
