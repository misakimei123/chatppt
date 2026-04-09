from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    def generate_structured(self, task_name: str, prompt: str, schema_name: str) -> dict[str, Any]:
        """Generate a structured result for a named task."""


class FakeLLMProvider:
    def __init__(self, response: dict[str, Any] | dict[str, dict[str, Any]]):
        self.response = response

    def generate_structured(self, task_name: str, prompt: str, schema_name: str) -> dict[str, Any]:
        if task_name in self.response:
            task_response = self.response[task_name]
            if isinstance(task_response, dict):
                return task_response
        if isinstance(self.response, dict):
            return self.response
        raise ValueError(f"No fake response configured for task: {task_name}")


class UnconfiguredLLMProvider:
    def generate_structured(self, task_name: str, prompt: str, schema_name: str) -> dict[str, Any]:
        raise RuntimeError(
            "No real LLM provider is configured. Inject a provider implementation before handling live traffic."
        )
