from __future__ import annotations

from chatppt.app.orchestration.state import ValidationReport


def validation_outcome(report: ValidationReport) -> str:
    if report.passed:
        return "pass"
    return "fail"
