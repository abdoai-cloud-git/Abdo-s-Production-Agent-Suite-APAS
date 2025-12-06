"""Core orchestrator for Abdo's Production Agent Suite."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Protocol

from pydantic import ValidationError

from .memory import OrchestratorMemory
from .schemas import (
    AgentName,
    AgentResult,
    AgentTask,
    PipelineRequest,
    PipelineResponse,
    TaskStatus,
    ToolName,
    ValidationResult,
)
from .task_router import TaskRouter


class OrchestratedAgent(Protocol):
    """Protocol that every orchestrated agent must follow."""

    name: AgentName
    allowed_tools: List[ToolName]

    def run(self, task: AgentTask, memory: OrchestratorMemory) -> AgentResult:  # pragma: no cover - protocol definition
        """Execute the provided task and return an `AgentResult`."""


class APASOrchestrator:
    """Routes tasks between agents, validates outputs, and enforces JSON schemas."""

    def __init__(
        self,
        router: Optional[TaskRouter] = None,
        memory: Optional[OrchestratorMemory] = None,
        max_retries: int = 2,
    ) -> None:
        self.router = router or TaskRouter()
        self.memory = memory or OrchestratorMemory()
        self.max_retries = max_retries
        self._agents: Dict[AgentName, OrchestratedAgent] = {}

    def register_agent(self, agent: OrchestratedAgent) -> None:
        self._agents[agent.name] = agent

    def dispatch_task(self, task: AgentTask, max_retries: Optional[int] = None) -> AgentResult:
        retries = self.max_retries if max_retries is None else max_retries
        self.memory.record_task(task)
        agent = self._get_agent(task.agent)
        attempts = 0
        last_result: Optional[AgentResult] = None

        while attempts <= retries:
            attempts += 1
            result = agent.run(task, self.memory)
            if not isinstance(result.output, dict):
                result.output = {"value": result.output}
            validation, normalized_output = self._validate(task, result.output)
            result.validation = validation
            result.attempts = attempts
            if validation.is_valid:
                if normalized_output is not None:
                    result.output = normalized_output
                result.status = TaskStatus.SUCCEEDED
                self.memory.record_result(result)
                return result

            result.status = TaskStatus.FAILED
            result.output["validation_errors"] = validation.errors
            self.memory.record_result(result)
            last_result = result

            if attempts > retries:
                break

            task = self._augment_task_with_errors(task, validation.errors, attempts)

        raise RuntimeError(
            "Task failed after retries",
        ) from (None if last_result is None else ValueError(repr(last_result.output)))

    def run_sequence(self, tasks: Iterable[AgentTask]) -> List[AgentResult]:
        return [self.dispatch_task(task) for task in tasks]

    def run_pipeline(self, request: PipelineRequest) -> PipelineResponse:
        routes = self.router.describe_pipeline(request.pipeline)
        aggregate: Dict[str, Any] = {}
        statuses: List[TaskStatus] = []

        for route in routes:
            instructions = route.description.format_map(_SafeDict(request.inputs))
            task = AgentTask(
                agent=route.agent,
                instructions=instructions,
                input_data=request.inputs,
                expected_output=route.expected_output,
            )
            result = self.dispatch_task(task, max_retries=route.max_retries)
            aggregate[route.name] = result.output
            statuses.append(result.status)

        status = TaskStatus.SUCCEEDED if all(s == TaskStatus.SUCCEEDED for s in statuses) else TaskStatus.FAILED
        return PipelineResponse(
            pipeline=request.pipeline,
            status=status,
            result=aggregate,
            metadata={"steps": [route.name for route in routes]},
        )

    def collaborative_loop(
        self,
        tasks: List[AgentTask],
        rounds: int = 2,
    ) -> List[AgentResult]:
        """Runs a multi-agent loop where outputs from prior tasks feed subsequent agents."""

        results: List[AgentResult] = []
        for _ in range(rounds):
            for task in tasks:
                last_result = self.memory.get_last_result()
                if last_result is not None:
                    task.metadata.setdefault("previous_output", last_result.output)
                results.append(self.dispatch_task(task))
        return results

    def _get_agent(self, name: AgentName) -> OrchestratedAgent:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' has not been registered")
        return self._agents[name]

    def _validate(
        self,
        task: AgentTask,
        output: Dict[str, Any],
    ) -> tuple[ValidationResult, Optional[Dict[str, Any]]]:
        schema = task.expected_output
        if schema is None:
            return ValidationResult(is_valid=True), output

        try:
            parsed = schema.model_validate(output)
        except ValidationError as exc:  # pragma: no cover - relies on pydantic internals
            errors = [f"{'/'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors()]
            return ValidationResult(is_valid=False, errors=errors), None

        return ValidationResult(is_valid=True), parsed.model_dump()

    @staticmethod
    def _augment_task_with_errors(task: AgentTask, errors: List[str], attempt: int) -> AgentTask:
        error_block = "\n".join(f"- {err}" for err in errors)
        revised_instructions = (
            f"{task.instructions}\n\n"
            f"Previous attempt #{attempt} produced schema violations. Address the following issues before responding again:\n"
            f"{error_block}"
        )
        return AgentTask(
            agent=task.agent,
            instructions=revised_instructions,
            input_data=task.input_data,
            expected_output=task.expected_output,
            metadata={**task.metadata, "retry": attempt},
        )


class _SafeDict(dict):
    """Helper that returns placeholder markers when formatting strings."""

    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive guard
        return "{" + key + "}"
