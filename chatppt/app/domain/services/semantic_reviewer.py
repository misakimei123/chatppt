from __future__ import annotations

from chatppt.app.domain.models.deck_ir import DeckIR
from chatppt.app.domain.models.evidence_pack import EvidencePack
from chatppt.app.orchestration.state import SemanticFinding


class SemanticReviewer:
    HIGH_CONFIDENCE_PATTERNS = ("already won", "guaranteed", "certain", "dominate the market")

    def review(self, deck: DeckIR, evidence_pack: EvidencePack) -> list[SemanticFinding]:
        evidence_refs = {fact.fact_id for fact in evidence_pack.facts}
        findings: list[SemanticFinding] = []
        for slide in deck.slides:
            for block in slide.content_blocks:
                lowered = block.text.lower()
                if (not block.evidence_refs or not set(block.evidence_refs).intersection(evidence_refs)) and any(
                    pattern in lowered for pattern in self.HIGH_CONFIDENCE_PATTERNS
                ):
                    findings.append(
                        SemanticFinding(
                            code="unsupported_claim",
                            message="The slide makes a strong conclusion without evidence support.",
                            slide_id=slide.slide_id,
                            severity="warning",
                        )
                    )
        return findings
