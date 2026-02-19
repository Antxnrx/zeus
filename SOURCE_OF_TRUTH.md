# SOURCE OF TRUTH (SoT)

This document is the canonical contract for the Autonomous CI/CD Healing Agent.
It reconciles and links:
- `README.md`
- `architecture.txt`
- `user-flow.txt`
- `db-architecture.txt`

If any of those files diverge, this SoT is authoritative.

## 1. System Purpose

The system autonomously takes a GitHub repo URL, detects failures, generates and validates fixes, commits to a new branch, monitors CI, retries/rolls back when needed, and returns final run artifacts (`results.json`, `report.pdf`) with full replayability.

## 2. Canonical Architecture

Eight layers:
1. Client: React dashboard (Vite) on Vercel.
2. API Gateway: Node.js + Express + Socket.io on Railway.
3. Queue: BullMQ on Redis/Upstash.
4. Orchestration: FastAPI + LangGraph.
5. Agent nodes: repo scan -> analysis -> fix -> critic -> commit -> CI monitor -> rollback/adversarial/self-benchmark.
6. Execution sandbox: language-specific Docker containers with network isolation (`--network none`).
7. External APIs: OpenAI, Anthropic, Gemini, GitHub.
8. Persistence: PostgreSQL + ChromaDB + Redis + filesystem outputs.

## 3. Canonical End-to-End Flow

Phases and linkage:
1. Submission (`user-flow` Phase 1): Dashboard -> `POST /run-agent` -> BullMQ enqueue -> room `/run/:runId`.
2. Security scan (`user-flow` Phase 2): pre-clone scan; unsafe repos are quarantined and halted.
3. Analysis (`user-flow` Phase 3): AST parse, dependency graph, test execution, topological ordering.
4. Fix loop (`user-flow` Phase 4): KB lookup first, else 3-LLM consensus, critic gate, commit optimizer.
5. CI loop (`user-flow` Phase 5): poll GitHub Actions; pass/rollback/retry branches with max iteration limit.
6. Hardening (`user-flow` Phase 6): adversarial test generation and final benchmark/evolution.
7. Completion (`user-flow` Phase 7): write outputs, emit `run_complete`, enable replay/interrogation/export.

Loop-backs:
- Critic reject: `critic_agent -> fix_generator`.
- CI fail with retries left: `ci_monitor -> fix_generator`.
- Regression: `ci_monitor -> rollback_agent -> fix_generator`.

## 4. Canonical API Contracts

External (Gateway-facing):
- `POST /run-agent`
- `GET /results/:runId`
- `GET /replay/:runId`
- `POST /agent/query`
- `GET /agent/status/:runId`
- `GET /health`

Internal (Gateway/worker to FastAPI):
- `POST /agent/start`
- `GET /agent/status`
- `GET /agent/stream`
- `POST /agent/query`

WebSocket:
- Room/namespace: `/run/:runId`
- Events: `thought_event`, `fix_applied`, `ci_update`, `telemetry_tick`, `run_complete`

## 5. Canonical Data Contracts

### PostgreSQL (system of record)

Tables:
- `runs`: one row per run lifecycle.
- `fixes`: one row per fix attempt/apply outcome.
- `ci_events`: one row per CI iteration.
- `execution_traces`: ordered replay events and reasoning.
- `strategy_weights`: GA-evolved strategy weights by bug type.
- `benchmark_scores`: rubric-level predicted vs actual score rows.

Status enums:
- Run status: `queued | running | passed | failed | quarantined`
- Fix status: `applied | failed | rolled_back | skipped`
- CI status: `pending | running | passed | failed`

### ChromaDB (learning memory)

Collections:
- `fix_patterns`: CI-confirmed successful fix embeddings only.
- `adversarial_tests`: generated edge-case test embeddings.

Rule:
- Rolled-back fixes are never embedded.

### Redis (ephemeral state)

Namespaces:
- BullMQ keys (`bull:*`) for queue mechanics.
- Run cache (`run:{run_id}:*`) for live status/score/node/telemetry.
- Event buffer (`events:{run_id}`) for late-join replay.
- Session/rate-limit/lock keys.

TTL:
- Run cache: 2h.
- Event buffer: 30m.
- Session: 24h.

### Filesystem (run artifacts)

Per run:
- `/outputs/{run_id}/results.json`
- `/outputs/{run_id}/report.pdf`

## 6. Integration Map (How Files Link Together)

`README.md` -> product + setup + public API intent.
`architecture.txt` -> service topology and runtime orchestration.
`user-flow.txt` -> precise execution sequence and decision gates.
`db-architecture.txt` -> persistence contracts, keyspaces, retention, query patterns.

Cross-linking:
1. Every major `user-flow` step maps to one or more LangGraph nodes in `architecture.txt`.
2. Each node transition/event in `architecture.txt` maps to writes defined in `db-architecture.txt`.
3. User-visible UI states in `README.md` are fed by WebSocket events and data reads from Redis/Postgres/filesystem.
4. Learning loop is closed by `fixes` + CI outcome -> Chroma upsert rules -> future KB hits.

## 7. Canonical Conventions (Resolved Mismatches)

1. Confidence score representation:
- Storage (`fixes.confidence_score`): `0.0` to `1.0`.
- UI display: percentage (`0` to `100%`).

2. Socket path:
- Canonical run channel is `/run/:runId`.

3. Trace authority:
- Replay and post-run Q&A use `execution_traces` in PostgreSQL as source of truth (not filesystem logs).

4. Output writing order:
- `results.json` is written at run completion.
- `report.pdf` is generated asynchronously after results are available.

5. Branch naming:
- `TEAM_NAME_LEADER_NAME_AI_Fix` (uppercase, underscores, suffix `_AI_Fix`).

6. Knowledge-base write gate:
- Only CI-confirmed successful fixes are added to `fix_patterns`.

## 8. Minimum Required Configuration

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `GITHUB_PAT`
- `DATABASE_URL`
- `REDIS_URL`
- `CHROMA_HOST`
- `CHROMA_PORT`
- `OUTPUT_DIR`

## 9. Non-Negotiable Invariants

1. No direct writes to `main`/`master`; all fixes go to generated AI fix branch.
2. Sandbox execution must remain network-isolated.
3. Quarantined repos must not execute code.
4. Retry loops are bounded by configured max iterations.
5. Replay fidelity requires append-only ordered `execution_traces` per run.

## 10. Ownership and Update Rule

When architecture/flow/schema changes:
1. Update this SoT first.
2. Then propagate updates to `README.md`, `architecture.txt`, `user-flow.txt`, and `db-architecture.txt`.
3. Treat mismatches as documentation bugs.

