"""Typed schemas for the content agent."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ContentIdea(BaseModel):
    day_index: int = Field(..., ge=1, description="Sequential day number within the calendar window")
    date: Optional[date] = Field(default=None, description="Optional absolute date for the post")
    theme: str
    hook: str
    content_type: str = Field(..., description="e.g., short-form video, carousel, newsletter")
    primary_channel: str
    supporting_channels: List[str] = Field(default_factory=list)
    call_to_action: str
    assets_needed: List[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Risks, dependencies, or assumptions")


class ContentCalendarDraft(BaseModel):
    brand: str
    niche: str
    objectives: List[str]
    tone: str
    pillars: List[str] = Field(..., description="Strategic pillars guiding the plan")
    cadence_per_week: int = Field(..., ge=1)
    total_days: int = Field(..., ge=1)
    channel_mix: List[str]
    ideas: List[ContentIdea]


class IdeationContext(BaseModel):
    brand: str
    niche: str
    objectives: List[str]
    tone: str = ""
    days: int
    channels: List[str] = Field(default_factory=list)
    reference_summaries: List[str] = Field(default_factory=list)
