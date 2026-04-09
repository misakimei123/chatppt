from __future__ import annotations

from collections import Counter


class Telemetry:
    def __init__(self):
        self.counters: Counter[str] = Counter()

    def increment(self, metric: str) -> None:
        self.counters[metric] += 1
