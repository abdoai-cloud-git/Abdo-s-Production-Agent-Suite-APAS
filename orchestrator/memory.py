"""State container for orchestrator executions."""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List, Optional

from .schemas import AgentName, AgentResult, AgentTask


class OrchestratorMemory:
    """Lightweight, threadsafe memory for sharing state across tasks."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._tasks: List[AgentTask] = []
        self._results: Dict[str, AgentResult] = {}
        self._state: Dict[str, Any] = {}

    def record_task(self, task: AgentTask) -> None:
        with self._lock:
            self._tasks.append(task)

    def record_result(self, result: AgentResult) -> None:
        with self._lock:
            self._results[result.task_id] = result

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        with self._lock:
            return next((task for task in self._tasks if task.task_id == task_id), None)

    def get_last_result(self, agent: Optional[AgentName] = None) -> Optional[AgentResult]:
        with self._lock:
            results = list(self._results.values())
            if agent is None:
                return results[-1] if results else None
            for result in reversed(results):
                if result.agent == agent:
                    return result
            return None

    def set_state(self, key: str, value: Any) -> None:
        with self._lock:
            self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def dump(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tasks": [task.model_dump() for task in self._tasks],
                "results": {k: v.model_dump() for k, v in self._results.items()},
                "state": dict(self._state),
            }
