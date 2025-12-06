"""Reviewer agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from orchestrator import AgentName, AgentResult, AgentTask, ToolName
from orchestrator.memory import OrchestratorMemory

from agents.base import BaseAPASAgent
from .schemas import ReviewPackage

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"


class ReviewerAgent(BaseAPASAgent):
    def __init__(self, *, model: str = "gpt-4.1-mini") -> None:
        super().__init__(
            name=AgentName.REVIEWER,
            system_prompt_path=PROMPT_PATH,
            model=model,
            temperature=0.15,
        )
        self.allowed_tools = [
            ToolName.CSV_READER,
            ToolName.PDF_READER,
            ToolName.IMAGE_READER,
            ToolName.WEBSITE_SCRAPER,
        ]

    def run(self, task: AgentTask, memory: OrchestratorMemory) -> AgentResult:
        schema = task.expected_output or ReviewPackage
        context = self._build_context(task, memory)
        structured = self._structured_completion(task=task, schema=schema, context=context)
        memory.set_state("review_notes", structured.get("summary", {}).get("risks", []))
        return self._result(task, structured)

    def _build_context(self, task: AgentTask, memory: OrchestratorMemory) -> Dict[str, Any]:
        data = task.input_data
        context: Dict[str, Any] = {
            "artifact_name": data.get("artifact_name", "deliverable"),
            "objectives": data.get("objectives", []),
            "brand_voice": data.get("brand_voice", ""),
            "artifact": data.get("artifact"),
            "channels": data.get("channels", []),
            "reference_summaries": data.get("reference_summaries", []),
        }
        latest_plan = memory.get_state("content_last_plan")
        if latest_plan and not context.get("artifact"):
            context["artifact"] = latest_plan
        return context
