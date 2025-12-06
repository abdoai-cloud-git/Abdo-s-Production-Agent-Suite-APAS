"""Content agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from orchestrator import AgentName, AgentTask, AgentResult, ToolName
from orchestrator.memory import OrchestratorMemory

from agents.base import BaseAPASAgent
from .schemas import ContentCalendarDraft, IdeationContext

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"


class ContentAgent(BaseAPASAgent):
    def __init__(self, *, model: str = "gpt-4.1-mini") -> None:
        super().__init__(
            name=AgentName.CONTENT,
            system_prompt_path=PROMPT_PATH,
            model=model,
            temperature=0.35,
        )
        self.allowed_tools = [
            ToolName.CSV_READER,
            ToolName.PDF_READER,
            ToolName.IMAGE_READER,
            ToolName.YT_TRANSCRIPT,
            ToolName.WEBSITE_SCRAPER,
        ]

    def run(self, task: AgentTask, memory: OrchestratorMemory) -> AgentResult:
        schema = task.expected_output or ContentCalendarDraft
        context = self._build_context(task, memory)
        structured = self._structured_completion(task=task, schema=schema, context=context)
        memory.set_state("content_last_plan", structured)
        return self._result(task, structured)

    def _build_context(self, task: AgentTask, memory: OrchestratorMemory) -> Dict[str, Any]:
        data = task.input_data
        ctx = IdeationContext(
            brand=data.get("brand", "Unknown brand"),
            niche=data.get("niche", "general"),
            objectives=data.get("objectives", []),
            tone=data.get("tone", ""),
            days=int(data.get("days", 30)),
            channels=data.get("channels", []),
            reference_summaries=data.get("reference_summaries", []),
        )
        prior_feedback = memory.get_state("review_notes", [])
        if prior_feedback:
            ctx.reference_summaries.extend(prior_feedback)
        return ctx.model_dump()
