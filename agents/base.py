"""Base classes and utilities for APAS agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from orchestrator import AgentName, AgentResult, AgentTask, TaskStatus, ToolName
from orchestrator.memory import OrchestratorMemory

load_dotenv()


class BaseAPASAgent:
    """Shared functionality for APAS agents."""

    def __init__(
        self,
        *,
        name: AgentName,
        system_prompt_path: Path,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
    ) -> None:
        self.name = name
        self.model = model
        self.temperature = temperature
        self.allowed_tools: list[ToolName] = []
        self._system_prompt = Path(system_prompt_path).read_text(encoding="utf-8").strip()
        self._client = OpenAI()

    def run(self, task: AgentTask, memory: OrchestratorMemory) -> AgentResult:  # pragma: no cover - interface only
        raise NotImplementedError

    def _structured_completion(
        self,
        *,
        task: AgentTask,
        schema: Type[BaseModel],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = self._build_payload(task.instructions, context)
        try:
            response = self._client.responses.create(
                model=self.model,
                input=payload,
                temperature=self.temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": True,
                    },
                },
            )
        except OpenAIError as exc:  # pragma: no cover - network call
            raise RuntimeError(f"OpenAI call failed for agent '{self.name.value}': {exc}") from exc

        content = self._extract_response_text(response)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - depends on model output
            raise RuntimeError("LLM returned invalid JSON") from exc

    def _build_payload(self, instructions: str, context: Optional[Dict[str, Any]]) -> list[Dict[str, Any]]:
        payload: list[Dict[str, Any]] = [
            {
                "role": "system",
                "content": [{"type": "text", "text": self._system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": instructions}],
            },
        ]

        if context:
            context_blob = json.dumps(context, ensure_ascii=False, indent=2)
            payload.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Contextual data to respect:\n{context_blob}",
                        }
                    ],
                }
            )
        return payload

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        for item in getattr(response, "output", []):
            for piece in getattr(item, "content", []):
                if getattr(piece, "type", None) == "output_text":
                    return piece.text.strip()
                if getattr(piece, "type", None) == "text":  # pragma: no cover - future proofing
                    return piece.text.strip()
        raise RuntimeError("LLM response did not include text output")

    def _result(self, task: AgentTask, output: Dict[str, Any]) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent=self.name,
            status=TaskStatus.RUNNING,
            output=output,
        )
