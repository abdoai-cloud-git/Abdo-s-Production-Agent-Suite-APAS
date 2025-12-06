"""Typed schemas for the APAS orchestrator."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Type
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class AgentName(str, Enum):
    """Identifiers for all orchestrated agents."""

    ORCHESTRATOR = "orchestrator"
    CONTENT = "content"
    ANALYTICS = "analytics"
    REVIEWER = "reviewer"


class ToolName(str, Enum):
    """Supported tool identifiers."""

    CSV_READER = "csv_reader"
    PDF_READER = "pdf_reader"
    IMAGE_READER = "image_reader"
    YT_TRANSCRIPT = "yt_transcript"
    WEBSITE_SCRAPER = "website_scraper"
    PDF_EXPORT = "pdf_export"
    SLIDES_EXPORT = "slides_export"
    EMAIL_SENDER = "email_sender"
    WEBHOOK_TRIGGER = "webhook_trigger"
    MAKE_CLIENT = "make_client"
    N8N_CLIENT = "n8n_client"


class TaskStatus(str, Enum):
    """Execution state of a task."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ValidationResult(BaseModel):
    """Represents validation output for a task payload."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_valid: bool
    errors: List[str] = Field(default_factory=list)


class AgentTask(BaseModel):
    """Normalized task contract consumed by agents."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent: AgentName
    instructions: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[Type[BaseModel]] = Field(
        default=None,
        description="Pydantic model used to validate the agent's response.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """Response envelope returned by agents after execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str
    agent: AgentName
    status: TaskStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResult = Field(default_factory=lambda: ValidationResult(is_valid=True))
    attempts: int = 1
    raw_response: Optional[str] = None


class TaskRoute(BaseModel):
    """Declarative description of a pipeline step."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    agent: AgentName
    description: str = ""
    expected_output: Optional[Type[BaseModel]] = None
    max_retries: int = 2
    requires: List[str] = Field(
        default_factory=list,
        description="Names of previous steps whose outputs feed this task.",
    )


class PipelineRequest(BaseModel):
    """Incoming API request to run a pipeline."""

    pipeline: str
    inputs: Dict[str, Any]


class PipelineResponse(BaseModel):
    """Normalized pipeline response envelope."""

    pipeline: str
    status: TaskStatus
    result: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
