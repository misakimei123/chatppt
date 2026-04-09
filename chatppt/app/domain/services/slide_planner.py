from __future__ import annotations

from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
from chatppt.app.domain.models.deck_ir import DeckIR, SlideContentBlock, SlideIR, VisualSlot
from chatppt.app.domain.models.deck_outline import DeckOutline
from chatppt.app.domain.models.evidence_pack import EvidencePack


class SlidePlanner:
    def plan(self, spec: ClarifiedSpec, outline: DeckOutline, pack: EvidencePack) -> DeckIR:
        fact_lookup = {fact.fact_id: fact for fact in pack.facts}
        slides: list[SlideIR] = []
        for index, section in enumerate(outline.sections, start=1):
            evidence_refs = section.evidence_refs
            evidence_claims = [fact_lookup[ref].claim for ref in evidence_refs if ref in fact_lookup]
            title = spec.topic if section.purpose == "title" else section.title
            content_blocks = self._build_content_blocks(index, section.purpose, evidence_claims, evidence_refs, spec)
            visual_slots = self._build_visual_slots(index, section.purpose)
            slides.append(
                SlideIR(
                    slide_id=f"slide-{index}",
                    section_id=section.section_id,
                    purpose=section.purpose,
                    title=title,
                    content_blocks=content_blocks,
                    visual_slots=visual_slots,
                    allowed_edit_operations=[
                        "rewrite_tone",
                        "fill_visual",
                        "swap_template",
                        "reorder_slides",
                        "delete_slide",
                    ],
                )
            )
        return DeckIR(slides=slides)

    @staticmethod
    def _build_content_blocks(
        index: int,
        purpose: str,
        evidence_claims: list[str],
        evidence_refs: list[str],
        spec: ClarifiedSpec,
    ) -> list[SlideContentBlock]:
        if purpose == "title":
            return [
                SlideContentBlock(
                    block_id=f"block-{index}-1",
                    kind="bullet",
                    text=f"Audience: {spec.audience}",
                    evidence_refs=[],
                )
            ]
        if evidence_claims:
            return [
                SlideContentBlock(
                    block_id=f"block-{index}-{claim_index}",
                    kind="stat" if purpose == "data" else "bullet",
                    text=claim,
                    evidence_refs=evidence_refs,
                )
                for claim_index, claim in enumerate(evidence_claims, start=1)
            ]
        return [
            SlideContentBlock(
                block_id=f"block-{index}-1",
                kind="bullet",
                text=f"{purpose.title()} summary for {spec.topic}",
                evidence_refs=[],
            )
        ]

    @staticmethod
    def _build_visual_slots(index: int, purpose: str) -> list[VisualSlot]:
        if purpose != "data":
            return []
        return [
            VisualSlot(
                slot_id=f"visual-{index}-1",
                kind="chart",
                semantic_description="Chart that reinforces the key quantitative takeaway.",
            )
        ]
