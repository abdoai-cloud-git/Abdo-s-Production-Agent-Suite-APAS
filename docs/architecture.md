# Abdo's Production Agent Suite (APAS) Architecture

## Core Principles

- Centralized orchestration with deterministic JSON schemas and retry/validation loops
- Modular agents (content, analytics, reviewer) that provide reasoning + tool invocation only
- Stateless tools grouped by capability domains (parsing, scraping, export, automation)
- Pipelines compose orchestrator + agents + tools to deliver business workflows
- FastAPI server exposes pipelines with JSON-first contracts for programmatic consumption

## System Topology

```
┌─────────────┐    ┌────────────────┐    ┌────────────────┐
│ FastAPI API │───▶│ Pipeline Layer │───▶│ APAS Orchestrator│
└─────────────┘    └────────────────┘    └────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 ▼                 ▼
                         Specialized Agents   Shared Tools
                                 │                 │
                                 └────────┬────────┘
                                          ▼
                                   Validation/Export
```

## Module Responsibilities

### Orchestrator (`/orchestrator`)

| File | Responsibility |
| --- | --- |
| `schemas.py` | Pydantic models for agent IDs, tasks, tool calls, validation errors, pipeline requests/responses |
| `memory.py` | Lightweight state container that tracks task context, prior outputs, retry counts |
| `task_router.py` | Deterministic routing logic that maps pipeline stages to agent sequences, including fallback strategies |
| `orchestrator.py` | `APASOrchestrator` class that executes routed tasks, enforces JSON schemas, performs validation + retries, and coordinates collaborations between agents |

### Agents (`/agents/<name>`)

- `agent.py`: Implements a typed `BaseAgent` subclass with `run(task: AgentTask) -> AgentResult`
- `prompts/`: Contains markdown prompt templates (system + reviewer instructions) used to construct LLM requests
- `schemas.py`: Defines agent-specific input/output models that the orchestrator references for validation
- Each agent exposes `allowed_tools` so the orchestrator can attach scoped tool adapters

### Tools (`/tools`)

- `file_parsing`: CSV, PDF, and image readers that convert files to structured JSON payloads
- `scraping`: Deterministic scrapers (YouTube transcripts, generic websites) with rate limiting + sanitization
- `export`: Generators that produce PDF or slide decks for finalized assets
- `automation`: Connectors for outbound actions (SMTP email, generic webhooks, Make.com, n8n)
- All tools are stateless, rely on env vars for credentials, and return schema-validated dicts

### Pipelines (`/pipelines`)

- Functions/classes that assemble orchestrator tasks for business workflows
- `content_calendar.py` (priority) calls Content → Reviewer agents, persists outputs, and optionally triggers exports
- `brand_strategy.py` and `analytics_report.py` will extend the same pattern once enabled

### Server (`/server`)

- `api.py`: FastAPI router exposing `/run_pipeline` with strong request/response models
- `main.py`: Application entry point + Uvicorn bootstrap helper

### Documentation (`/docs`)

- `architecture.md`: This document; kept up-to-date with design decisions
- `pipelines.md`: JSON contracts for each pipeline, including required inputs + expected outputs

## Data Flow

1. Client submits `PipelineInvocation` via FastAPI.
2. Pipeline module shapes orchestrator tasks (ordered agent stages + validation rules).
3. `APASOrchestrator` delegates each stage to the appropriate agent via `TaskRouter`.
4. Agent builds LLM call using its prompt templates, optionally invoking allowed tools to gather context.
5. Orchestrator validates the agent response against the declared schema. On failure, it retries with augmented context.
6. Pipeline aggregates validated outputs, adds export artifacts when requested, and emits a JSON response.

## Priority Roadmap (from requirements)

1. Orchestrator module (schemas, memory, router, orchestrator implementation)
2. Content agent (agent runtime, prompts, schemas)
3. File parsing tools (CSV, PDF, Image)
4. `content_calendar` pipeline (leverages orchestrator + agents + parsing tools)
5. FastAPI server (`api.py`, `main.py`)
6. Additional agents (analytics, reviewer) and additional pipelines (brand strategy, analytics report)

Each milestone will include unit-level tests or executable examples plus documentation updates to guarantee production readiness.
