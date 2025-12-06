"""Analytics agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from orchestrator import AgentName, AgentResult, AgentTask, ToolName
from orchestrator.memory import OrchestratorMemory

from agents.base import BaseAPASAgent
from .schemas import AnalyticsReport

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system.md"


class AnalyticsAgent(BaseAPASAgent):
    def __init__(self, *, model: str = "gpt-4.1-mini") -> None:
        super().__init__(
            name=AgentName.ANALYTICS,
            system_prompt_path=PROMPT_PATH,
            model=model,
            temperature=0.25,
        )
        self.allowed_tools = [
            ToolName.CSV_READER,
            ToolName.PDF_READER,
            ToolName.YT_TRANSCRIPT,
            ToolName.WEBSITE_SCRAPER,
        ]

    def run(self, task: AgentTask, memory: OrchestratorMemory) -> AgentResult:
        schema = task.expected_output or AnalyticsReport
        context = self._build_context(task, memory)
        structured = self._structured_completion(task=task, schema=schema, context=context)
        memory.set_state("analytics_last_report", structured)
        return self._result(task, structured)

    def _build_context(self, task: AgentTask, memory: OrchestratorMemory) -> Dict[str, Any]:
        data = task.input_data
        context: Dict[str, Any] = {
            "timeframe": data.get("timeframe", "last 30 days"),
            "primary_goal": data.get("primary_goal", "growth"),
            "segments": data.get("segments", []),
            "datasets": data.get("datasets", []),
            "raw_metrics": data.get("raw_metrics", {}),
            "notes": data.get("notes", ""),
        }
        prior = memory.get_state("analytics_last_report")
        if prior:
            context["previous_report"] = prior
        return context
