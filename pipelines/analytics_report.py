"""Analytics report pipeline."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from agents.analytics import AnalyticsAgent
from agents.analytics.schemas import AnalyticsReport
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
from tools.export import PDFExporter


class AnalyticsReportInput(BaseModel):
    brand: str
    timeframe: str = "last 30 days"
    focus_metrics: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    reference_files: List[ReferenceFile] = Field(default_factory=list)
    perform_ocr: bool = True
    export_pdf: bool = False


class AnalyticsReportPipeline:
    def __init__(
        self,
        *,
        orchestrator: Optional[APASOrchestrator] = None,
        reference_ingestor: Optional[ReferenceIngestor] = None,
        pdf_exporter: Optional[PDFExporter] = None,
    ) -> None:
        router = TaskRouter()
        memory = OrchestratorMemory()
        self.orchestrator = orchestrator or APASOrchestrator(router=router, memory=memory)
        self.reference_ingestor = reference_ingestor or ReferenceIngestor()
        self.pdf_exporter = pdf_exporter or PDFExporter()
        self._ensure_agents()
        self._register_routes()

    def run(self, payload: AnalyticsReportInput) -> PipelineResponse:
        references = self.reference_ingestor.ingest(payload.reference_files, perform_ocr=payload.perform_ocr)
        analytics_task = AgentTask(
            agent=AgentName.ANALYTICS,
            instructions=(
                "Generate a KPI report highlighting the metrics supplied. Include trends, risks, and next actions."
            ),
            input_data={
                "brand": payload.brand,
                "timeframe": payload.timeframe,
                "segments": [],
                "raw_metrics": {},
                "notes": ", ".join(payload.focus_metrics),
                "reference_summaries": references,
            },
            expected_output=AnalyticsReport,
            metadata={"pipeline": "analytics_report", "step": "analysis"},
        )
        analytics_result = self.orchestrator.dispatch_task(analytics_task)

        review_task = AgentTask(
            agent=AgentName.REVIEWER,
            instructions="Review the analytics findings and ensure recommendations are actionable.",
            input_data={
                "artifact_name": "Analytics report",
                "artifact": analytics_result.output,
                "objectives": payload.objectives,
            },
            expected_output=ReviewPackage,
            metadata={"pipeline": "analytics_report", "step": "review"},
        )
        review_result = self.orchestrator.dispatch_task(review_task)

        exports = {}
        if payload.export_pdf:
            pdf_path = self.pdf_exporter.export_analytics_report(analytics_result.output)
            exports["pdf"] = pdf_path

        status = (
            TaskStatus.SUCCEEDED
            if all(result.status == TaskStatus.SUCCEEDED for result in (analytics_result, review_result))
            else TaskStatus.FAILED
        )

        return PipelineResponse(
            pipeline="analytics_report",
            status=status,
            result={
                "report": analytics_result.output,
                "review": review_result.output,
                "references": references,
                "exports": exports,
            },
            metadata={"steps": ["analysis", "review"]},
        )

    def _ensure_agents(self) -> None:
        self.orchestrator.register_agent(AnalyticsAgent())
        self.orchestrator.register_agent(ReviewerAgent())

    def _register_routes(self) -> None:
        routes = [
            TaskRoute(
                name="analysis",
                agent=AgentName.ANALYTICS,
                description="Prepare analytics report",
                expected_output=AnalyticsReport,
            ),
            TaskRoute(
                name="review",
                agent=AgentName.REVIEWER,
                description="Validate analytics report",
                expected_output=ReviewPackage,
            ),
        ]
        try:
            self.orchestrator.router.describe_pipeline("analytics_report")
        except KeyError:
            self.orchestrator.router.register_pipeline("analytics_report", routes)


def build_analytics_report_pipeline() -> AnalyticsReportPipeline:
    return AnalyticsReportPipeline()
