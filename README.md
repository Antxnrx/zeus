# 🤖 Autonomous CI/CD Healing Agent

> **RIFT 2026 Hackathon — AI/ML · DevOps Automation · Agentic Systems Track**
> An intelligent multi-agent system that autonomously detects, fixes, and verifies code failures in GitHub repositories — with a production-grade React dashboard as its primary interface.

---

## 🔗 Quick Links

| Resource | Link |
|---|---|
| 🌐 Live Deployed Dashboard | `https://your-app.vercel.app` |
| 📹 LinkedIn Demo Video | `https://linkedin.com/posts/your-demo` |
| 🐙 GitHub Repository | `https://github.com/your-team/rift-2026-agent` |
| 📄 Architecture Diagram | `/docs/architecture.png` |

---

## 📌 Table of Contents

1. [Project Overview](#project-overview)
2. [The Problem We Solve](#the-problem-we-solve)
3. [How It Works — High Level](#how-it-works--high-level)
4. [Feature Breakdown](#feature-breakdown)
5. [Architecture Deep Dive](#architecture-deep-dive)
6. [Agent Graph & Orchestration](#agent-graph--orchestration)
7. [React Dashboard](#react-dashboard)
8. [Tech Stack](#tech-stack)
9. [Supported Bug Types](#supported-bug-types)
10. [Branch Naming Convention](#branch-naming-convention)
11. [Scoring System](#scoring-system)
12. [Installation & Local Setup](#installation--local-setup)
13. [Environment Variables](#environment-variables)
14. [Usage Guide](#usage-guide)
15. [API Reference](#api-reference)
16. [Known Limitations](#known-limitations)
17. [Team Members](#team-members)

---

## Project Overview

The **Autonomous CI/CD Healing Agent** is a full-stack, production-grade system built for the RIFT 2026 Hackathon. It accepts a GitHub repository URL as input, autonomously clones and analyzes the repository, discovers and runs all test files, identifies every failure, generates targeted fixes, commits them with an `[AI-AGENT]` prefix to a new branch, monitors the CI/CD pipeline, and iterates until all tests pass — all without any human intervention.

The system is powered by a **multi-agent LangGraph orchestration layer** running on Python/FastAPI, a **Node.js + Express API gateway**, a **BullMQ job queue backed by Redis**, language-specific **Docker execution sandboxes**, a **multi-model LLM consensus engine** using OpenAI, Anthropic, and Google Gemini, a **ChromaDB vector knowledge base** that learns from every run, and a **PostgreSQL persistence layer** storing full replay traces and strategy evolution data.

All of this is surfaced through a **React dashboard** deployed on Vercel — the primary interface judges interact with.

---

## The Problem We Solve

Modern software development is bottlenecked not by the speed of writing code, but by the speed of fixing it. Studies show developers spend **40–60% of their working time** debugging CI/CD failures rather than building features. These failures range from trivial linting issues to deep logic bugs spanning multiple interconnected files. Every failed pipeline means context switching, manual diagnosis, patching, re-pushing, and waiting — a cycle that compounds across teams and repos.

Existing solutions address this partially: linters catch syntax errors, static analyzers flag obvious issues, and Dependabot handles dependency vulnerabilities. But none of them close the full loop. None of them **reason** about why a bug exists, **order** fixes by dependency, **verify** a fix before committing it, **roll back** a regression automatically, or **learn** from past runs to improve on the next one.

Our agent does all of this. It treats CI/CD failure not as a notification to route to a developer, but as a problem to **autonomously resolve** end-to-end.

---

## How It Works — High Level

```
User submits GitHub repo URL via React Dashboard
              │
              ▼
  Express API enqueues job → BullMQ → FastAPI triggers LangGraph
              │
              ▼
  Repo Scanner     →  Malicious scan + secret detection + language detection
  AST Analyzer     →  Bug detection + dependency graph + risk heatmap
  Test Runner      →  Docker sandbox + capture all failures
  Fix Generator    →  ChromaDB KB lookup → 3-LLM consensus vote → sandbox verify
  Critic Agent     →  AST re-validate + confidence score + rejection logic
  Commit Optimizer →  Batch fixes + enforce [AI-AGENT] prefix + push branch
  CI Monitor       →  Poll GitHub Actions + regression detection + rollback
  Adversarial Test →  Write new edge-case tests for fixed code paths
  Self-Benchmarker →  Score run against rubric + evolve strategy weights
              │
              ▼
  results.json written + PDF report generated
  Full trace stored to PostgreSQL for Replay Mode
  Successful fix patterns embedded → stored in ChromaDB
              │
              ▼
  React Dashboard updates in real time via Socket.io
```

Every step emits events streamed live to the dashboard. Judges can watch the agent think, fix, commit, and verify — in real time.

---

## Feature Breakdown

### 🔍 Intelligence & Analysis

**Predictive Failure Detection**
Before running a single test, the agent performs a static analysis pass using cyclomatic complexity, dependency depth, and file-level risk scoring. Results are displayed as a color-coded risk heatmap on the dashboard, giving an immediate visual of codebase health before any fixes begin.

**Root Cause Chaining**
Instead of treating each bug in isolation, the agent builds a full dependency graph of all detected failures and resolves them in topological order. If `utils.py` is breaking `validator.py` which is breaking `main.py`, the agent fixes `utils.py` first — preventing wasted CI iterations from fixing downstream effects before their upstream causes.

**Causal Bug Attribution**
For every detected bug, the agent runs a lightweight `git blame` and recent commit diff analysis to trace when and why the bug was likely introduced. It generates a natural language explanation displayed as an insight card on the dashboard alongside each fix.

**AST-Based Fixes**
Every fix is generated using Abstract Syntax Tree parsing via `tree-sitter` (multi-language) and Python's `ast` module. This ensures fixes are structurally valid at the grammar level, not just textually plausible — dramatically improving accuracy on complex logic and type errors.

---

### 🤝 Multi-Agent Architecture

**Multi-Model Consensus Fixing**
For each detected bug, the fix request is sent simultaneously to three LLMs — GPT-4o, Claude Sonnet, and Gemini Flash. A voting algorithm selects the fix at least two models agree on. When all three disagree, a meta-arbitrator agent makes the final call. This approach eliminates hallucinated or structurally broken fixes that a single model might produce with confidence.

**Cost-Aware Model Routing**
Simple bugs like linting violations and indentation errors are routed to cheap fast models (GPT-4o-mini, Gemini Flash). Complex logic errors, type errors, and import chain issues are escalated to GPT-4o or Claude Sonnet. A live agent cost meter on the dashboard tracks total token spend across all models in real time.

**Self-Reflective Fix Verification (Critic Agent)**
Every fix produced by the Fix Generator is passed to a dedicated Critic Agent before being committed. The Critic re-validates the fix using AST parsing, scores regression risk, and assigns a confidence score between 0 and 100%. Fixes below the confidence threshold are rejected and the Fix Generator retries with an alternative strategy or model.

**Counterfactual Fix Simulation**
Before any fix is committed, the agent applies it inside a sandboxed subprocess and captures the actual test outcome. It then compares this against its predicted outcome. If reality and prediction diverge, the fix is flagged as low-confidence and retried — the agent is essentially testing its own reasoning before acting on it.

**Dynamic Agent Spawning**
On cloning, the agent analyzes the module dependency graph and partitions it into clusters of related files. One specialized sub-agent is spawned per cluster, each independently fixing its assigned modules in parallel. A merge coordinator resolves cross-cluster conflicts before the final push — enabling true parallel fixing rather than sequential processing.

---

### 🧠 Learning & Memory

**Fix Knowledge Base with Vector Search**
Successful fix patterns are stored as vector embeddings in ChromaDB using OpenAI's `text-embedding-3-small` model. Before every LLM call, the agent performs a semantic similarity search against this knowledge base. On a match, the fix is applied instantly without an LLM call, and a "Pattern Match ⚡" badge is shown in the fixes table. The agent becomes measurably faster with every run.

**Agent Memory Across Repos**
The knowledge base is not scoped to a single repo or team — it is shared across all runs throughout the hackathon. The agent builds a cross-repo bug signature library. Any time it recognizes a recurring antipattern from a previous submission by any team, it resolves it instantly.

**Fix Strategy Evolution**
The agent tracks which fixing strategies worked best for which bug types across runs and uses a simple genetic algorithm to evolve the strategy weight matrix stored in PostgreSQL. Over time, the agent biases toward AST rewriting for type errors, line replacement for linting, and full function regeneration for logic bugs — automatically. A Strategy Evolution chart on the dashboard visualizes this drift.

---

### 🔄 CI/CD & Git Operations

**Adaptive Retry Strategy**
Instead of a fixed retry counter, the agent uses exponential backoff with jitter between CI iterations. After each failure it evaluates whether to retry with the same fix, roll back and try a different strategy, or escalate to a more capable model — driven by the failure pattern rather than a simple counter.

**Rollback Intelligence**
If a committed fix causes a previously passing test to fail (a regression), the agent detects this via CI diff analysis and issues a targeted `git revert` on only that specific commit. The regression is logged as its own entry on the CI/CD timeline. The agent then retries with an alternative approach — it does not simply pile more commits on top of a broken state.

**Speculative Branch Execution**
When the agent is genuinely uncertain between two fix strategies, it creates both branches simultaneously, pushes both to the remote, and waits for CI results on both in parallel. Whichever branch passes is auto-merged. The failed branch is deleted and logged. This trades one extra branch for parallelism, which can help beat the five-minute speed bonus.

**CI/CD Pipeline Mutation**
Most agents only touch application code. This agent also inspects `.github/workflows` YAML files, Dockerfiles, and Makefiles. If it detects misconfigured pipeline steps, missing dependencies, or incorrect environment variables in the CI definition itself, it fixes those too — logged as `PIPELINE_CONFIG` bug type in the fixes table.

**Adversarial Test Generation**
After all bugs are fixed and CI passes, a dedicated sub-agent writes new edge-case unit tests specifically targeting the fixed code paths. These are committed and CI runs one final time. The agent is not just patching to satisfy existing tests — it is actively hardening the codebase.

---

### 🔐 Security

**Malicious Repo Detection**
Before cloning any repository, the agent pre-scans it via the GitHub API for red flags including unusually large binary files, obfuscated source code, exposed `.env` files with real credentials, and test scripts that attempt external network calls. Flagged repos are quarantined and a security alert card is shown on the dashboard — the agent never executes code from a suspicious repo.

**Secret Scanning as a Bug Type**
The agent actively scans all source files for hardcoded secrets including API keys, tokens, database passwords, and private certificates using `detect-secrets` (entropy analysis + pattern matching) and `Bandit`. When found, they are classified as `SECRET_LEAK` in the fixes table, replaced with environment variable references, and committed with a security badge.

**Sandboxed Network Egress Control**
Every language sandbox container is launched with Docker's `--network none` flag, giving it zero outbound internet access during test execution. This prevents any test or script in the analyzed repo from making external calls. A "Network Isolated ✓" badge is displayed on the dashboard run summary.

---

### 📊 Dashboard & Observability

**Live Agent Thought Stream**
Every agent decision, tool call, retry, and branch evaluation is streamed to the dashboard in real time via WebSocket. Judges watch the agent reason through problems as they happen — not just the final result.

**3D Codebase Dependency Graph**
The entire repository is rendered as an interactive 3D node graph using Three.js. Nodes represent files, edges represent import relationships, node color represents bug density (green → red), and node size represents fix complexity. Judges can rotate, zoom, and click nodes to view fix history and causal attribution cards.

**Temporal Fix Heatmap Calendar**
A GitHub contribution calendar-style heatmap shows how bug density changed across each CI iteration from start to finish — colored from deep red (many failures) to solid green (clean pass). Judges see at a glance how efficiently the agent converged.

**Confidence Score Column**
Every fix in the table shows a 0–100% confidence score computed from model consensus level, AST validity result, sandbox simulation outcome, and knowledge base match status. Low-confidence fixes show a warning icon with a tooltip.

**Live Resource Telemetry Panel**
Real-time CPU usage, memory consumption, and Docker container stats are streamed to the dashboard as animated sparkline charts via WebSocket using `psutil`. This signals production-grade infrastructure observability.

**Natural Language Agent Interrogation**
After a run completes, judges can type questions directly to the agent — "Why did you fix validator.py before utils.py?" — and receive answers grounded in the stored execution trace.

**Replay Mode**
The full execution trace is persisted in PostgreSQL. Judges can enter Replay Mode and step through every agent action, tool call, fix decision, CI result, and rollback event at their own pace.

**Agent Self-Benchmarking**
After every run, the agent programmatically scores itself against the hackathon rubric and displays both its predicted score and the actual computed score. The calibration gap between self-score and actual score is displayed as a metacognition metric.

**Shareable PDF Report**
A fully formatted PDF report is auto-generated at the end of every run using Puppeteer, containing the complete fixes table, CI/CD timeline, score breakdown, causal attribution insights, and confidence scores.

**Multi-Repo Comparison Mode**
Multiple GitHub URLs can be submitted simultaneously. The agent runs independent instances in parallel and the dashboard displays side-by-side results — showcasing the scalability of the underlying architecture.

---

## Architecture Deep Dive

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                             │
│          React + Vite Dashboard (Vercel)                     │
│   Zustand · React Query · Socket.io · Three.js · Recharts    │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP REST / WebSocket
┌─────────────────────▼────────────────────────────────────────┐
│                   API GATEWAY                                │
│            Node.js + Express (Railway)                       │
│         Socket.io Server · Session Store (Redis)             │
└─────────────────────┬────────────────────────────────────────┘
                      │ BullMQ Enqueue
┌─────────────────────▼────────────────────────────────────────┐
│                    JOB QUEUE                                 │
│            BullMQ + Redis / Upstash                          │
│         Concurrency: 3 · Exponential Backoff                 │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP → FastAPI trigger
┌─────────────────────▼────────────────────────────────────────┐
│                ORCHESTRATION LAYER                           │
│           FastAPI + LangGraph (Railway / Python)             │
│  AgentState · 11-node directed graph · conditional routing   │
└────┬──────────┬──────────┬──────────┬───────────────┬────────┘
     │          │          │          │               │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌──────▼──────┐
│ Repo   │ │  AST   │ │  Fix   │ │ Critic  │ │  CI Monitor │
│Scanner │ │Analyzer│ │ Agent  │ │  Agent  │ │  + Rollback │
└────────┘ └────────┘ └────────┘ └─────────┘ └─────────────┘
                          │
              ┌───────────▼───────────┐
              │  EXECUTION SANDBOX    │
              │  Docker (network=none)│
              │  Python · Node · Java │
              └───────────────────────┘
                          │
         ┌────────────────┼────────────────┐
┌────────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
│  OpenAI API   │ │Anthropic API │ │  Gemini API  │
│GPT-4o / mini  │ │Claude Sonnet │ │  1.5 Flash   │
└───────────────┘ └──────────────┘ └──────────────┘
                          │
         ┌────────────────┼────────────────┐
┌────────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
│  PostgreSQL   │ │   ChromaDB   │ │    GitHub    │
│  (Railway)    │ │  Vector KB   │ │  REST API    │
└───────────────┘ └──────────────┘ └──────────────┘
```

### Service Communication

| From | To | Protocol |
|---|---|---|
| React Dashboard | Express API | HTTP REST (JSON) |
| Express API | React Dashboard | WebSocket (Socket.io) |
| Express API | BullMQ | Redis enqueue |
| BullMQ Worker | FastAPI | HTTP REST |
| FastAPI | Socket.io Server | Internal SSE bridge |
| LangGraph Nodes | LLM APIs | HTTPS REST (parallel) |
| Agent | Docker Sandboxes | Docker SDK (subprocess) |
| Sandbox Containers | Agent | stdout / stderr capture |
| Agent | GitHub API | HTTPS REST (PAT auth) |
| Agent | ChromaDB | HTTP (local service) |
| Agent | PostgreSQL | SQLAlchemy (TCP) |
| psutil | Socket.io Stream | Polling → WS emit |

---

## Agent Graph & Orchestration

The agent is implemented as a **stateful directed graph** using LangGraph. Each node is a specialized sub-agent. The graph routes conditionally based on the shared `AgentState` object passed between nodes.

### LangGraph Nodes

| Node | Role |
|---|---|
| `repo_scanner` | Malicious pre-scan, secret detection, language detection, cluster partitioning |
| `ast_analyzer` | Multi-language AST parsing, risk scoring, dependency mapping, causal attribution |
| `test_runner` | Docker sandbox spawn, test execution, failure capture, telemetry stream |
| `dependency_mapper` | Topological ordering of fix sequence by dependency depth |
| `fix_generator` | ChromaDB KB lookup → 3-LLM parallel call → consensus vote → simulation |
| `critic_agent` | AST re-validation, confidence scoring, fix rejection and retry trigger |
| `commit_optimizer` | Fix batching, commit message enforcement, branch push |
| `ci_monitor` | GitHub Actions polling, regression detection, retry orchestration |
| `rollback_agent` | Targeted `git revert`, regression logging, alternative strategy trigger |
| `adversarial_tester` | Edge-case test generation, final CI run |
| `self_benchmarker` | Rubric scoring, strategy weight update, PDF report trigger |

### AgentState Object

```python
class AgentState(TypedDict):
    repo_url:           str
    team_name:          str
    leader_name:        str
    branch_name:        str
    run_id:             str
    failures:           List[BugReport]
    fixes:              List[FixResult]
    iteration_count:    int
    max_iterations:     int
    cost_tracker:       Dict[str, float]
    confidence_scores:  Dict[str, float]
    execution_trace:    List[TraceEvent]
    strategy_weights:   Dict[str, float]
    results_json:       Dict
    quarantine_flag:    bool
    start_time:         float
```

---

## React Dashboard

The dashboard is the **primary evaluation interface** for judges. It is fully responsive, deployed on Vercel, and updates in real time via WebSocket.

### Panels

**Input Section**
GitHub repository URL, team name, team leader name, and a Run Agent button with a loading indicator during execution.

**Run Summary Card**
Repository URL, team info, branch name created, total failures detected, total fixes applied, final CI/CD status badge (PASSED / FAILED), and total time taken.

**Score Breakdown Panel**
Base score (100), speed bonus applied (+10 if under 5 minutes), efficiency penalty (−2 per commit over 20), and final total score displayed with a visual progress bar.

**Fixes Applied Table**
Columns: File · Bug Type · Line Number · Commit Message · Confidence Score · Status. Color coded green for success, red for failure. Clicking any row expands an inline Monaco-powered diff viewer.

**CI/CD Status Timeline**
Each CI/CD iteration shown with pass/fail badge, timestamp, iteration number out of retry limit, and regression/rollback events.

**Live Agent Thought Stream**
Real-time log of agent reasoning, tool calls, and decisions streamed via WebSocket.

**3D Dependency Graph**
Interactive Three.js graph of the entire repo structure with bug density coloring. Clickable nodes show fix history.

**Heatmap Calendar**
Bug density per CI iteration visualized as a contribution-style calendar from red to green.

**Live Telemetry Panel**
CPU and memory sparklines for running Docker containers, updated every second.

**Natural Language Interrogation**
Post-run chat interface to ask the agent questions about its decisions.

**Replay Mode**
Step-by-step playback of the full execution trace.

**PDF Export**
Downloadable run report generated by Puppeteer containing all results in formatted layout.

---

## Tech Stack

### Frontend
| Tool | Purpose |
|---|---|
| React + Vite | UI framework |
| TailwindCSS | Styling |
| Zustand | State management |
| TanStack React Query | API data fetching + caching |
| Socket.io Client | Real-time WebSocket events |
| Three.js + react-force-graph-3d | 3D dependency graph |
| Recharts | Charts, heatmaps, sparklines |
| Monaco Editor | Inline diff viewer |
| Framer Motion | Animations and transitions |
| @react-pdf/renderer | Client-side PDF export |
| Deployment: Vercel | Free tier hosting |

### Backend — API Gateway
| Tool | Purpose |
|---|---|
| Node.js + Express | REST API server |
| Socket.io Server | WebSocket broadcaster |
| BullMQ | Job queue producer + consumer |
| Upstash Redis | BullMQ backing store + cache |
| Deployment: Railway | Free tier hosting |

### Backend — Agent Service
| Tool | Purpose |
|---|---|
| FastAPI | Python API microservice |
| LangGraph | Multi-agent orchestration |
| GitPython | Git operations (clone, branch, commit, push, revert) |
| PyGithub | GitHub REST API wrapper |
| Docker SDK for Python | Sandbox container management |
| psutil | Container telemetry collection |
| SQLAlchemy + Alembic | ORM and database migrations |
| Puppeteer (via Node) | Server-side PDF rendering |
| Deployment: Railway | Free tier hosting |

### Code Analysis
| Tool | Purpose |
|---|---|
| tree-sitter | Multi-language AST parsing |
| ast (stdlib) | Python-specific deep AST analysis |
| Pylint + Flake8 | Python linting inside sandbox |
| Black | Python auto-formatting |
| ESLint + Prettier | JavaScript / TypeScript linting |
| Bandit | Python security scanning |
| detect-secrets | Hardcoded secret detection |

### AI / LLM
| Tool | Purpose |
|---|---|
| OpenAI GPT-4o | Complex logic and type error fixes |
| OpenAI GPT-4o-mini | Simple linting and syntax fixes |
| OpenAI text-embedding-3-small | Fix pattern embeddings for ChromaDB |
| Anthropic Claude Sonnet | Consensus voter #2 |
| Google Gemini 1.5 Flash | Consensus voter #3 |

### Data
| Tool | Purpose |
|---|---|
| PostgreSQL (Railway) | Primary database — runs, fixes, traces, strategy weights |
| ChromaDB | Vector database — fix knowledge base |
| Redis / Upstash | Queue backing store + active run cache |

---

## Supported Bug Types

| Bug Type | Description | Example |
|---|---|---|
| `LINTING` | Unused imports, line length, style violations | Unused import `os` in line 15 |
| `SYNTAX` | Missing colons, brackets, quotes, indentation blocks | Missing colon after `if` condition |
| `LOGIC` | Incorrect conditions, wrong operators, off-by-one errors | `>` should be `>=` in loop boundary |
| `TYPE_ERROR` | Wrong types passed, missing type annotations, None checks | `str` passed where `int` expected |
| `IMPORT` | Missing imports, circular imports, wrong module paths | `from utils import helper` not found |
| `INDENTATION` | Mixed tabs/spaces, incorrect indent level | Function body at wrong indent depth |
| `PIPELINE_CONFIG` | Misconfigured CI/CD workflows, Dockerfiles, Makefiles | Missing `pip install` step in workflow |
| `SECRET_LEAK` | Hardcoded API keys, tokens, passwords, certificates | AWS key hardcoded in config file |

---

## Branch Naming Convention

All branches created by the agent follow this exact format:

```
TEAM_NAME_LEADER_NAME_AI_Fix
```

Rules:
- All uppercase
- Spaces replaced with underscores
- Must end with `_AI_Fix`
- No special characters except underscores
- Never pushed to `main` or `master`

Examples:

| Team Name | Leader Name | Branch Created |
|---|---|---|
| RIFT ORGANISERS | Saiyam Kumar | `RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix` |
| Code Warriors | John Doe | `CODE_WARRIORS_JOHN_DOE_AI_Fix` |
| Neural Ninjas | Priya Sharma | `NEURAL_NINJAS_PRIYA_SHARMA_AI_Fix` |

---

## Scoring System

```
Base Score          :  100 points
Speed Bonus         :  +10  (if total time < 5 minutes)
Efficiency Penalty  :  -2   per commit over 20
─────────────────────────────────────────
Final Score         :  Base + Bonus - Penalty
```

The dashboard displays a live score simulation that updates in real time as fixes are applied and commits are pushed. The score breakdown panel includes a visual progress bar and a self-benchmarked predicted score alongside the computed actual score.

Strategies the agent uses to maximize score:
- **Commit Optimizer Agent** batches related fixes to minimize total commit count
- **Speculative Branch Execution** runs CI in parallel to save time
- **ChromaDB KB** resolves known patterns instantly, cutting LLM latency
- **Topological fix ordering** prevents unnecessary retry iterations

---

## Installation & Local Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-team/rift-2026-agent.git
cd rift-2026-agent
```

### 2. Set Up the Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Fill in VITE_API_URL and VITE_SOCKET_URL
npm run dev
```

### 3. Set Up the API Gateway (Node.js)

```bash
cd backend/gateway
npm install
cp .env.example .env
# Fill in all environment variables (see section below)
npm run dev
```

### 4. Set Up the Agent Service (Python / FastAPI)

```bash
cd backend/agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in all environment variables
uvicorn main:app --reload --port 8001
```

### 5. Start ChromaDB

```bash
pip install chromadb
chroma run --path ./chroma_data --port 8002
```

### 6. Run Database Migrations

```bash
cd backend/agent
alembic upgrade head
```

### 7. Start BullMQ Worker

```bash
cd backend/gateway
npm run worker
```

### 8. Verify Everything is Running

| Service | URL |
|---|---|
| React Dashboard | http://localhost:5173 |
| Express API Gateway | http://localhost:3000 |
| FastAPI Agent Service | http://localhost:8001 |
| ChromaDB | http://localhost:8002 |

---

## Environment Variables

### Frontend (`frontend/.env.local`)

```env
VITE_API_URL=http://localhost:3000
VITE_SOCKET_URL=http://localhost:3000
```

### API Gateway (`backend/gateway/.env`)

```env
PORT=3000
FASTAPI_URL=http://localhost:8001
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://localhost:6379
SESSION_SECRET=your_secret_here
```

### Agent Service (`backend/agent/.env`)

```env
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# GitHub
GITHUB_PAT=ghp_...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rift_agent
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8002

# Internal URLs
GATEWAY_SOCKET_URL=http://localhost:3000

# Agent Config
AGENT_MAX_RETRIES=5
AGENT_WORKER_CONCURRENCY=3
AGENT_CONFIDENCE_THRESHOLD=70
AGENT_MAX_PARALLEL_BRANCHES=2
```

---

## Usage Guide

### Running the Agent via Dashboard

1. Open the deployed dashboard at your Vercel URL (or `http://localhost:5173` locally)
2. Enter the GitHub repository URL you want to analyze
3. Enter your team name (e.g. `RIFT ORGANISERS`)
4. Enter your team leader name (e.g. `Saiyam Kumar`)
5. Click **Run Agent**
6. Watch the live thought stream and telemetry panels update in real time
7. View the fixes table as commits are pushed
8. Monitor the CI/CD timeline for each iteration
9. Download the PDF report when the run completes

### Running via API

```bash
curl -X POST https://your-api.railway.app/run-agent \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/example/test-repo",
    "team_name": "RIFT ORGANISERS",
    "leader_name": "Saiyam Kumar"
  }'
```

Response:
```json
{
  "run_id": "run_abc123",
  "branch_name": "RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix",
  "status": "queued",
  "socket_room": "/run/run_abc123"
}
```

### Fetching Results

```bash
curl https://your-api.railway.app/results/run_abc123
```

### Natural Language Interrogation (Post-run)

```bash
curl -X POST https://your-api.railway.app/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_abc123",
    "question": "Why did you fix utils.py before validator.py?"
  }'
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/run-agent` | Submit a repo for analysis, returns runId |
| GET | `/results/:runId` | Fetch completed results.json |
| GET | `/replay/:runId` | Fetch full execution trace for Replay Mode |
| POST | `/agent/query` | Natural language question about a completed run |
| GET | `/agent/status/:runId` | Current agent node and iteration count |
| GET | `/health` | Service health check |

**WebSocket Events (Socket.io — room `/run/:runId`)**

| Event | Payload | Description |
|---|---|---|
| `thought_event` | `{ node, message, timestamp }` | Agent reasoning step |
| `fix_applied` | `{ file, bug_type, line, confidence, commit_sha }` | Fix committed |
| `ci_update` | `{ iteration, status, timestamp, regression }` | CI run result |
| `telemetry_tick` | `{ cpu_pct, mem_mb, container }` | Container resource stats |
| `run_complete` | `{ score, fixes_count, total_time, pdf_url }` | Run finished |

---

## Known Limitations

- **Private repositories** require the submitted GitHub PAT to have read/write access to the target repo. Public repos work with any valid PAT.
- **Monorepos** with more than 50 modules may exceed the free tier Railway memory limit. Recommended to increase worker memory or reduce `AGENT_WORKER_CONCURRENCY` to 1.
- **Test files must be auto-discoverable** — the agent uses standard test discovery conventions (`test_*.py`, `*.test.js`, `*_spec.rb`). Unconventionally named test files may be missed.
- **Speculative branch execution** doubles GitHub Actions usage. On free-tier GitHub accounts with limited Actions minutes, this feature can be disabled via `AGENT_ENABLE_SPECULATIVE_BRANCHES=false`.
- **LLM costs** are covered by free tier credits during the hackathon. For high-volume testing, monitor your OpenAI and Anthropic dashboards to avoid exceeding free limits.
- **ChromaDB** is self-hosted and resets if the Railway service is restarted without a persistent volume mounted. For the hackathon demo, this is acceptable. Production deployments should mount a persistent disk.
- **PDF generation** via Puppeteer adds 15–20 seconds to total run time. This does not affect the score timer, which stops when CI passes.
- **Java, Go, and Rust** sandbox support is functional but less battle-tested than Python and Node.js sandboxes. Edge cases in exotic build configurations may not be handled.

---

## Team Members

| Name | Role |
|---|---|
| [Team Leader Name] | Agent Architecture + LangGraph Orchestration |
| [Member 2 Name] | React Dashboard + WebSocket Integration |
| [Member 3 Name] | Docker Sandbox + Code Analysis Pipeline |
| [Member 4 Name] | LLM Integration + ChromaDB Knowledge Base |

---

## Acknowledgements

Built for **RIFT 2026 Hackathon** — AI/ML · DevOps Automation · Agentic Systems Track.

Powered by LangGraph, OpenAI, Anthropic, Google Gemini, React, FastAPI, and Docker.

---

*Last updated: February 2026*
