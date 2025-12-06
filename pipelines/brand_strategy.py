"""Brand strategy pipeline."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError

from agents.analytics import AnalyticsAgent
from agents.analytics.schemas import AnalyticsReport
from agents.content import ContentAgent
from agents.reviewer import ReviewerAgent
from agents.reviewer.schemas import ReviewPackage
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


class MessagingPillar(BaseModel):
    name: str
    description: str
    proof_points: List[str]
    recommended_channels: List[str]


class BrandStrategyDraft(BaseModel):
    positioning_statement: str
    narrative_frames: List[str]
    pillars: List[MessagingPillar]
    activation_ideas: List[str]


class BrandStrategyInput(BaseModel):
    brand: str
    mission: str
    target_audience: str
    differentiators: List[str]
    objectives: List[str]
    channels: List[str] = Field(default_factory=list)
    reference_files: List[ReferenceFile] = Field(default_factory=list)
    perform_ocr: bool = True


class BrandStrategyPipeline:
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

    def run(self, payload: BrandStrategyInput) -> PipelineResponse:
        references = self.reference_ingestor.ingest(payload.reference_files, perform_ocr=payload.perform_ocr)

        analytics_task = AgentTask(
            agent=AgentName.ANALYTICS,
            instructions=(
                "Audit the available references to surface differentiators, unmet needs, and channel opportunities. "
                "Prioritize evidence-backed findings."
            ),
            input_data={
                "brand": payload.brand,
                "primary_goal": payload.objectives[0] if payload.objectives else "growth",
                "raw_metrics": {},
                "notes": payload.mission,
                "reference_summaries": references,
            },
            expected_output=AnalyticsReport,
            metadata={"pipeline": "brand_strategy", "step": "analytics"},
        )
        analytics_result = self.orchestrator.dispatch_task(analytics_task)

        strategy_task = AgentTask(
            agent=AgentName.CONTENT,
            instructions=(
                "Using the analytics findings, craft a positioning statement and 3-4 messaging pillars with proof points. "
                "Tie each pillar to recommended channels and activation ideas."
            ),
            input_data={
                "brand": payload.brand,
                "niche": payload.target_audience,
                "objectives": payload.objectives,
                "channels": payload.channels,
                "reference_summaries": references,
                "analytics_report": analytics_result.output,
            },
            expected_output=BrandStrategyDraft,
            metadata={"pipeline": "brand_strategy", "step": "strategy"},
        )
        strategy_result = self.orchestrator.dispatch_task(strategy_task)

        review_task = AgentTask(
            agent=AgentName.REVIEWER,
            instructions="Review the brand strategy for clarity, feasibility, and differentiation.",
            input_data={
                "artifact_name": "Brand strategy",
                "artifact": strategy_result.output,
                "objectives": payload.objectives,
                "brand_voice": payload.mission,
                "channels": payload.channels,
            },
            expected_output=ReviewPackage,
            metadata={"pipeline": "brand_strategy", "step": "review"},
        )
        review_result = self.orchestrator.dispatch_task(review_task)

        response = {
            "strategy": strategy_result.output,
            "analytics": analytics_result.output,
            "review": review_result.output,
            "references": references,
        }
        status = (
            TaskStatus.SUCCEEDED
            if all(
                result.status == TaskStatus.SUCCEEDED
                for result in (analytics_result, strategy_result, review_result)
            )
            else TaskStatus.FAILED
        )
        return PipelineResponse(
            pipeline="brand_strategy",
            status=status,
            result=response,
            metadata={"steps": ["analytics", "strategy", "review"]},
        )

    def _ensure_agents(self) -> None:
        self.orchestrator.register_agent(AnalyticsAgent())
        self.orchestrator.register_agent(ContentAgent())
        self.orchestrator.register_agent(ReviewerAgent())

    def _register_routes(self) -> None:
        routes = [
            TaskRoute(
                name="brand_analytics",
                agent=AgentName.ANALYTICS,
                description="Analyze references for strategic insights.",
                expected_output=AnalyticsReport,
            ),
            TaskRoute(
                name="strategy_draft",
                agent=AgentName.CONTENT,
                description="Draft positioning and pillars.",
                expected_output=BrandStrategyDraft,
            ),
            TaskRoute(
                name="strategy_review",
                agent=AgentName.REVIEWER,
                description="QA the brand strategy deliverable.",
                expected_output=ReviewPackage,
            ),
        ]
        try:
            self.orchestrator.router.describe_pipeline("brand_strategy")
        except KeyError:
            self.orchestrator.router.register_pipeline("brand_strategy", routes)


def build_brand_strategy_pipeline() -> BrandStrategyPipeline:
    return BrandStrategyPipeline()
