"""Content calendar pipeline implementation."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError

from agents.content import ContentAgent
from agents.content.schemas import ContentCalendarDraft
from orchestrator import (
    APASOrchestrator,
    AgentName,
    AgentTask,
    PipelineResponse,
    TaskRoute,
    TaskStatus,
)
from orchestrator.memory import OrchestratorMemory
from orchestrator.task_router import TaskRouter
from pipelines.shared import ReferenceFile, ReferenceIngestor


class ContentCalendarInput(BaseModel):
    brand: str
    niche: str
    days: int = Field(default=30, ge=7)
    tone: str = ""
    objectives: List[str] = Field(default_factory=list)
    channels: List[str] = Field(default_factory=list)
    reference_files: List[ReferenceFile] = Field(default_factory=list)
    perform_ocr: bool = True


class ContentCalendarResponse(BaseModel):
    brand: str
    niche: str
    days: int
    calendar: ContentCalendarDraft
    references: List[str]


class ContentCalendarPipeline:
    def __init__(
        self,
        *,
        orchestrator: Optional[APASOrchestrator] = None,
        reference_ingestor: Optional[ReferenceIngestor] = None,
    ) -> None:
        router = TaskRouter()
        memory = OrchestratorMemory()
        self.orchestrator = orchestrator or APASOrchestrator(router=router, memory=memory)
        self.reference_ingestor = reference_ingestor or ReferenceIngestor()
        self._ensure_agents()
        self._register_routes()

    def run(self, payload: ContentCalendarInput) -> PipelineResponse:
        references = self.reference_ingestor.ingest(payload.reference_files, perform_ocr=payload.perform_ocr)
        task = AgentTask(
            agent=AgentName.CONTENT,
            instructions=self._build_instructions(payload),
            input_data={
                "brand": payload.brand,
                "niche": payload.niche,
                "days": payload.days,
                "tone": payload.tone,
                "objectives": payload.objectives,
                "channels": payload.channels,
                "reference_summaries": references,
            },
            expected_output=ContentCalendarDraft,
            metadata={"pipeline": "content_calendar"},
        )
        result = self.orchestrator.dispatch_task(task, max_retries=3)
        try:
            calendar = ContentCalendarDraft.model_validate(result.output)
        except ValidationError as exc:
            raise RuntimeError("Agent output failed schema validation") from exc

        response = ContentCalendarResponse(
            brand=payload.brand,
            niche=payload.niche,
            days=payload.days,
            calendar=calendar,
            references=references,
        )
        return PipelineResponse(
            pipeline="content_calendar",
            status=TaskStatus.SUCCEEDED,
            result=response.model_dump(),
            metadata={"reference_count": len(references)},
        )

    def _build_instructions(self, payload: ContentCalendarInput) -> str:
        objectives_text = "\n".join(f"- {goal}" for goal in payload.objectives) or "- Maintain engagement"
        channels = payload.channels or ["instagram", "tiktok", "newsletter"]
        return (
            "You are drafting a {days}-day content calendar for {brand} in the {niche} space. "
            "Incorporate the tone '{tone}' and prioritize the following objectives:\n"
            f"{objectives_text}\n"
            f"Plan for the channels: {', '.join(channels)}. Include campaign pillars, hooks, CTA, and asset needs."
        ).format(
            days=payload.days,
            brand=payload.brand,
            niche=payload.niche,
            tone=payload.tone or "brand-consistent",
        )

    def _ensure_agents(self) -> None:
        self.orchestrator.register_agent(ContentAgent())

    def _register_routes(self) -> None:
        route = TaskRoute(
            name="content_plan",
            agent=AgentName.CONTENT,
            description="Produce a fully structured content calendar based on provided inputs.",
            expected_output=ContentCalendarDraft,
            max_retries=3,
        )
        try:
            self.orchestrator.router.describe_pipeline("content_calendar")
        except KeyError:
            self.orchestrator.router.register_pipeline("content_calendar", [route])


def build_content_calendar_pipeline() -> ContentCalendarPipeline:
    return ContentCalendarPipeline()
