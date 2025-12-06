"""Typed schemas for the reviewer agent."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ReviewFinding(BaseModel):
    category: str = Field(..., description="Aspect being reviewed, e.g., messaging, CTA, compliance")
    severity: str = Field(..., description="low/medium/high")
    comment: str
    recommendation: str


class ReviewSummary(BaseModel):
    overall_alignment: str
    ready_to_publish: bool
    risks: List[str] = Field(default_factory=list)


class ReviewPackage(BaseModel):
    artifact_name: str
    summary: ReviewSummary
    findings: List[ReviewFinding]
    follow_up_actions: List[str] = Field(default_factory=list)
