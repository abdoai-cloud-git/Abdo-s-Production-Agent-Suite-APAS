"""Typed schemas for the analytics agent."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class KPIInsight(BaseModel):
    metric: str
    value: float
    unit: str = Field(default="", description="%, $, etc")
    trend_vs_prior: str = Field(default="flat", description="up/down/flat")
    insight: str
    recommended_action: str


class AnalyticsSummary(BaseModel):
    timeframe: str
    primary_goal: str
    headline: str


class AnalyticsReport(BaseModel):
    summary: AnalyticsSummary
    kpis: List[KPIInsight]
    anomalies: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
