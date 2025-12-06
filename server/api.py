"""HTTP API layer for APAS."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Literal, Tuple, Type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError

from orchestrator import APASOrchestrator, PipelineResponse
from pipelines.analytics_report import AnalyticsReportInput, AnalyticsReportPipeline
from pipelines.brand_strategy import BrandStrategyInput, BrandStrategyPipeline
from pipelines.content_calendar import ContentCalendarInput, ContentCalendarPipeline

router = APIRouter(prefix="/v1", tags=["pipelines"])


class RunPipelineRequest(BaseModel):
    pipeline: Literal["content_calendar", "brand_strategy", "analytics_report"]
    inputs: Dict[str, Any]


class PipelineRegistry:
    """Keeps instantiated pipelines ready for API calls."""

    def __init__(self) -> None:
        orchestrator = APASOrchestrator()
        self._pipelines: Dict[str, Tuple[object, Type[BaseModel]]] = {
            "content_calendar": (ContentCalendarPipeline(orchestrator=orchestrator), ContentCalendarInput),
            "brand_strategy": (BrandStrategyPipeline(orchestrator=orchestrator), BrandStrategyInput),
            "analytics_report": (AnalyticsReportPipeline(orchestrator=orchestrator), AnalyticsReportInput),
        }

    def run(self, pipeline: str, raw_inputs: Dict[str, Any]) -> PipelineResponse:
        if pipeline not in self._pipelines:
            raise KeyError(f"Pipeline '{pipeline}' is not registered")
        pipeline_impl, input_model = self._pipelines[pipeline]
        typed_inputs = input_model.model_validate(raw_inputs)
        return pipeline_impl.run(typed_inputs)


@lru_cache(maxsize=1)
def get_registry() -> PipelineRegistry:
    return PipelineRegistry()


@router.get("/health", tags=["health"])
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/run_pipeline", response_model=PipelineResponse)
def run_pipeline_endpoint(
    payload: RunPipelineRequest,
    registry: PipelineRegistry = Depends(get_registry),
) -> PipelineResponse:
    try:
        return registry.run(payload.pipeline, payload.inputs)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
