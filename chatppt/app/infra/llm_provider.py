from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


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


class QwenProvider:
    """
    LLM Provider for Qwen (DashScope API / OpenAI-compatible interface).
    
    Features:
    - Supports generate_text() / generate_structured() / generate_with_tools() modes
    - Retry mechanism with exponential backoff
    - Token counting and logging
    - Reads configuration from environment variables
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model or os.getenv("LLM_MODEL", "qwen-plus")
        self.max_retries = max_retries
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY not set. QwenProvider may fail on actual requests.")
        
        self._client = httpx.Client(timeout=self.timeout)
        self._token_count = 0
        self._request_count = 0
    
    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _execute_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP request with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.post(
                    url=f"{self.base_url}/chat/completions",
                    headers=self._build_headers(),
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                
                # Update token count
                usage = result.get("usage", {})
                self._token_count += usage.get("total_tokens", 0)
                self._request_count += 1
                
                logger.info(
                    f"Request #{self._request_count} completed. "
                    f"Tokens used: {usage.get('total_tokens', 'N/A')}, "
                    f"Total tokens: {self._token_count}"
                )
                
                return result
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(f"HTTP error on attempt {attempt}: {e}. Response: {e.response.text}")
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt}: {e}")
            
            if attempt < self.max_retries:
                wait_time = 2 ** (attempt - 1)  # Exponential backoff
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        raise RuntimeError(f"Failed after {self.max_retries} attempts. Last error: {last_exception}")
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate plain text response from LLM.
        
        Args:
            prompt: User input prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text string
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        result = self._execute_request(payload)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content
    
    def generate_structured(
        self,
        task_name: str,
        prompt: str,
        schema_name: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Generate structured JSON response from LLM.
        
        Args:
            task_name: Name of the task (for logging)
            prompt: User input prompt
            schema_name: Name of expected output schema
            system_prompt: Optional system instruction
            temperature: Lower temperature for more deterministic output
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON dictionary
        """
        if system_prompt is None:
            system_prompt = (
                f"You are generating structured output for task '{task_name}'. "
                f"Output must be valid JSON conforming to schema '{schema_name}'. "
                "Respond ONLY with JSON, no additional text."
            )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        
        logger.info(f"Generating structured output for task: {task_name}")
        result = self._execute_request(payload)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        try:
            parsed = json.loads(content)
            logger.info(f"Successfully parsed JSON response for task: {task_name}")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}. Raw content: {content[:500]}")
            # Return empty dict or raise based on requirements
            return {}
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_prompt: str = "You are a helpful assistant with access to tools.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Generate response with tool calling capability.
        
        Args:
            prompt: User input prompt
            tools: List of tool definitions (OpenAI function format)
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dict containing either message or tool_calls
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "tool_choice": "auto",
        }
        
        logger.info(f"Generating response with {len(tools)} available tools")
        result = self._execute_request(payload)
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        response = {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
        }
        
        if response["tool_calls"]:
            logger.info(f"Model requested {len(response['tool_calls'])} tool calls")
        
        return response
    
    @property
    def token_count(self) -> int:
        """Get total tokens consumed."""
        return self._token_count
    
    @property
    def request_count(self) -> int:
        """Get total number of requests made."""
        return self._request_count
    
    def reset_stats(self) -> None:
        """Reset token and request counters."""
        self._token_count = 0
        self._request_count = 0
