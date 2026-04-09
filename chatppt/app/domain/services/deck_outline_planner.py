from __future__ import annotations

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.deck_outline import DeckOutline, DeckSection
from chatppt.app.domain.models.evidence_pack import EvidencePack


class DeckOutlinePlanner:
    def plan(self, spec: ClarifiedSpec, pack: EvidencePack) -> DeckOutline:
        max_slides = min(spec.expected_duration_minutes + 2, 10)
        sections: list[DeckSection] = [
            DeckSection(section_id="sec-1", title=spec.topic, purpose="title", evidence_refs=[]),
        ]
        fact_budget = max(0, max_slides - 2)
        for fact in pack.facts[:fact_budget]:
            sections.append(
                DeckSection(
                    section_id=f"sec-{len(sections) + 1}",
                    title=fact.claim,
                    purpose="data",
                    evidence_refs=[fact.fact_id],
                )
            )
        if not pack.facts:
            sections.append(
                DeckSection(
                    section_id=f"sec-{len(sections) + 1}",
                    title=f"{spec.topic} Overview",
                    purpose="problem" if spec.use_case != "board update" else "solution",
                    evidence_refs=[],
                )
            )
        sections.append(
            DeckSection(
                section_id=f"sec-{len(sections) + 1}",
                title="Recommendations",
                purpose="summary",
                evidence_refs=[fact.fact_id for fact in pack.facts[:1]],
            )
        )
        return DeckOutline(
            deck_objective=spec.topic,
            narrative_arc=self._narrative_arc_for(spec.use_case),
            estimated_slide_count=min(len(sections), max_slides),
            sections=sections[:max_slides],
        )

    @staticmethod
    def _narrative_arc_for(use_case: str) -> str:
        use_case = use_case.lower()
        if "pitch" in use_case or "strategy" in use_case:
            return "problem-solution-impact"
        if "board" in use_case:
            return "context-evidence-decision"
        return "overview-detail-summary"
