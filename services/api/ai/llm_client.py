"""LLM Provider abstraction supporting Gemini, OpenAI-compatible APIs, and Hermetic Mock."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    text: str
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate response given prompts and optional tool declarations."""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic, circuit-grounded mock provider for CI, testing, and offline use."""

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        # Extract ground-truth facts from the grounded prompt if present
        lines = user_prompt.splitlines()
        query = ""
        depth = "unknown"
        gates = "unknown"
        distribution = ""

        for line in lines:
            if line.startswith("User Query:"):
                query_idx = lines.index(line)
                if query_idx + 1 < len(lines):
                    query = lines[query_idx + 1]
            elif "Depth:" in line:
                depth = line.split("Depth:")[-1].strip()
            elif "Gates count:" in line:
                gates = line.split("Gates count:")[-1].strip()
            elif line.startswith("Simulation Measurement Distribution"):
                dist_idx = lines.index(line)
                if dist_idx + 1 < len(lines):
                    distribution = lines[dist_idx + 1]

        # Generate realistic, evidence-grounded response
        response_parts = [
            f"Based on the quantum circuit analysis and execution results:",
        ]

        if gates != "unknown":
            response_parts.append(
                f"- The circuit contains {gates} gate(s) with an analyzed circuit depth of {depth}."
            )

        if distribution:
            response_parts.append(
                f"- The simulation yielded the measurement distribution: {distribution}."
            )

        response_parts.append(
            "The quantum operations and measurement outcomes confirm the expected circuit behavior."
        )

        return LLMResponse(
            text="\n".join(response_parts),
            tool_calls=[],
        )


class GeminiProvider(LLMProvider):
    """Google Gemini API provider using httpx."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        }

        if tools:
            # Map tools to Gemini function declarations
            function_declarations = []
            for t in tools:
                function_declarations.append({
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {}),
                })
            payload["tools"] = [{"functionDeclarations": function_declarations}]

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self.endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(text="No response generated.")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        text_out = ""
        tool_calls: list[ToolCallRequest] = []

        for p in parts:
            if "text" in p:
                text_out += p["text"]
            if "functionCall" in p:
                fc = p["functionCall"]
                tool_calls.append(
                    ToolCallRequest(
                        name=fc["name"],
                        arguments=fc.get("args", {}),
                    )
                )

        return LLMResponse(text=text_out, tool_calls=tool_calls)


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible chat completion provider using httpx."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload: dict[str, Any] = {"model": self.model, "messages": messages}

        if tools:
            payload["tools"] = [
                {"type": "function", "function": t}
                for t in tools
            ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            return LLMResponse(text="No response generated.")

        message = choices[0].get("message", {})
        text_out = message.get("content") or ""
        tool_calls: list[ToolCallRequest] = []

        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            tool_calls.append(ToolCallRequest(name=fn.get("name", ""), arguments=args))

        return LLMResponse(text=text_out, tool_calls=tool_calls)


def get_llm_provider() -> LLMProvider:
    """Factory to instantiate the appropriate LLM provider based on environment variables."""
    provider_name = os.environ.get("LLM_PROVIDER", "").lower()

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if provider_name == "gemini" or (not provider_name and gemini_key):
        if gemini_key:
            model = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
            return GeminiProvider(api_key=gemini_key, model=model)

    openai_key = os.environ.get("OPENAI_API_KEY")
    if provider_name in ("openai", "openai-compatible") or (not provider_name and openai_key):
        if openai_key:
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.environ.get("LLM_MODEL", "gpt-4o")
            return OpenAICompatibleProvider(api_key=openai_key, base_url=base_url, model=model)

    return MockLLMProvider()
