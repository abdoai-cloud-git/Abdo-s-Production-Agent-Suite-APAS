"""Routing utilities for orchestrating multi-agent workflows."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .schemas import TaskRoute


class TaskRouter:
    """Maintains deterministic task sequences for each pipeline."""

    def __init__(self) -> None:
        self._pipelines: Dict[str, List[TaskRoute]] = {}

    def register_pipeline(self, pipeline: str, routes: Iterable[TaskRoute]) -> None:
        route_list = list(routes)
        if not route_list:
            raise ValueError("Route list cannot be empty")
        self._pipelines[pipeline] = route_list

    def describe_pipeline(self, pipeline: str) -> List[TaskRoute]:
        routes = self._pipelines.get(pipeline)
        if routes is None:
            raise KeyError(f"Pipeline '{pipeline}' has not been registered")
        return routes

    def get_route(self, pipeline: str, name: str) -> TaskRoute:
        for route in self.describe_pipeline(pipeline):
            if route.name == name:
                return route
        raise KeyError(f"Route '{name}' is not defined for pipeline '{pipeline}'")
