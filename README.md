# WES Showcase — Workstream Engagement System

A working, runnable showcase built for the **Senior Software Engineer**
role at **Kaufman Rossin & Co.** It implements every technology point in
the job description as real, tested code — not slideware — across three
services: a Python/FastAPI API, a Rust/Axum/Tonic performance engine,
and a React/TypeScript UI.

## 1. Project Synopsis

WES tracks **Workstreams** (units of engagement work) through Hermes
document intake and a Kanban-style lifecycle. Creating or transitioning
a Workstream:

1. Calls the **Rust/Tonic** engine to compute a risk/priority score
   (systems-level, latency-sensitive logic kept out of Python).
2. Publishes a `WorkstreamEvent` to **Azure Event Hubs**, reachable
   either natively (AMQP) or via its **Kafka-compatible** endpoint.
3. Broadcasts the same event over **Azure SignalR Service** (serverless
   mode) to every connected **React/TypeScript** client in real time.
4. Every API call is authorized via an **Azure Entra ID** (OAuth 2.0 /
   OIDC / JWT) bearer token.
5. A `/ai/search` and `/ai/ask` surface demonstrate **RAG** over Hermes
   documents (Azure AI Search + HelixDB + TensorZero-gateway pattern),
   including a **streaming** response handler.

Every Azure/cloud dependency has a documented, code-backed local
fallback (see §6), so `make up` runs the entire stack with **zero**
cloud subscriptions — while every production integration point is
still implemented, not just described.

## 2. Directory Structure

```
kr-wes-showcase/
├── backend/                     # WES API — Python + FastAPI
│   ├── app/
│   │   ├── main.py              # composition root
│   │   ├── core/                # config, Entra ID/JWT auth, logging
│   │   ├── models/               # Pydantic domain models
│   │   ├── routers/             # workstreams, ai (RAG), realtime_ws
│   │   ├── services/            # eventing, realtime, rust_client, rag
│   │   └── generated/           # grpc stubs (generated, see `make proto`)
│   ├── tests/                   # pytest
│   ├── requirements.txt / pyproject.toml / Dockerfile
├── rust-engine/                 # Performance engine — Rust + Axum + Tonic
│   ├── proto/risk.proto         # shared gRPC contract
│   ├── src/{main,http,grpc,risk}.rs
│   └── Cargo.toml / build.rs / Dockerfile
├── frontend/                    # WES UI — React + TypeScript
│   ├── src/
│   │   ├── App.tsx, main.tsx
│   │   ├── components/WorkstreamBoard.tsx
│   │   ├── store/workstreamStore.ts      # Zustand (client state)
│   │   ├── api/client.ts                 # fetch layer (React Query fuel)
│   │   └── hooks/{useAuth,useRealtimeWorkstreams}.ts
│   ├── package.json / vite.config.ts / tailwind.config.js / Dockerfile
├── docs/adr-0001-*.md, adr-0002-*.md      # Architecture Decision Records
├── .github/workflows/ci.yml               # GitHub Actions: 3 native pipelines
├── docker-compose.yml, Makefile
└── README.md
```

## 3. Build, Run & Test Instructions

### Fastest path — full stack, zero cloud deps
```bash
make up          # docker compose up --build  → :5173 UI, :8000 API, :8080/:50051 engine
```

### Native / per-service (also what CI runs)

**Rust engine** (compiles `proto/risk.proto` → Rust via `build.rs` automatically):
```bash
make rust-build   # cargo build --release
make rust-run      # cargo run           (Axum :8080, Tonic :50051)
make rust-test      # cargo test + clippy in CI
```

**Backend** (optionally transpile the same `.proto` → Python stubs first):
```bash
make backend-install
make proto          # python -m grpc_tools.protoc ... → app/generated/*_pb2*.py
make backend-run     # uvicorn app.main:app --reload --port 8000
make backend-test    # pytest -q
make backend-lint    # ruff check app
```
Auth in dev mode uses a locally-signed HS256 token (see
`backend/tests/test_workstreams.py::_dev_token`) so the API is callable
with zero Entra ID tenant configured; swap to RS256 + tenant JWKS by
setting the `WES_ENTRA_*` variables in `.env` (copy `.env.example`).

**Frontend**:
```bash
make frontend-install
make frontend-run     # vite dev server on :5173, proxies /api → :8000
make frontend-build    # tsc -b && vite build
make frontend-test     # vitest run
```

## 4. Solution Explanation

| Requirement | Where it's implemented |
|---|---|
| WES API (Python/FastAPI), WES UI (React/TS), Hermes, Workstreams | `backend/app/routers/workstreams.py`, `ai.py` (Hermes RAG); `frontend/src/components/WorkstreamBoard.tsx` |
| Business logic & AI workflows in Python/FastAPI | `routers/ai.py` streaming `/ask`, `services/rag.py` |
| Rust, Axum, Tonic performance-critical components | `rust-engine/src/{http,grpc,risk}.rs` — one scoring core, two protocol front-ends |
| React components w/ Tailwind + Radix | `frontend/tailwind.config.js`, `package.json` (`@radix-ui/react-dialog`), `WorkstreamBoard.tsx` |
| React Query (server state) + Zustand (client state), replacing Apollo/Redux | `WorkstreamBoard.tsx` (`useQuery`/`useMutation`) vs. `store/workstreamStore.ts` |
| Azure SignalR Service real-time | `backend/app/services/realtime.py` (`AzureSignalRBroadcaster` + local fallback), `frontend/src/hooks/useRealtimeWorkstreams.ts` |
| Azure Event Hubs + Kafka-compatible messaging | `backend/app/services/eventing.py` (`EventHubPublisher`, `KafkaCompatiblePublisher`) |
| Entra ID: OAuth 2.0 / OIDC / JWT | `backend/app/core/security.py` |
| Tech-debt reduction, migration plans | `docs/adr-0001-*.md`, `docs/adr-0002-*.md` |
| Native testing/linting per language | `backend/tests` (pytest), `rust-engine` `#[cfg(test)]` + clippy, `frontend` vitest/eslint |
| CI/CD | `.github/workflows/ci.yml` — 3 independent jobs, one per language |
| RAG: Azure AI Search + HelixDB + TensorZero, streaming responses | `backend/app/services/rag.py`, `routers/ai.py::ask` (`StreamingResponse`) |

## 5. UI/UX Wireframe (ASCII)

```
┌──────────────────────────────────────────────────────────────┐
│ WES · Workstreams                                  ● live    │
├──────────────────────────────────────────────────────────────┤
│ [all] [draft] [in_review] [approved] [blocked] [done]         │
│                                                                │
│ [ + New Workstream ]                                          │
│                                                                │
│ ┌────────────────────────────────────────────┐  risk         │
│ │ Migrate EKS to AKS               [blocked]  │  78.5   ← ring│
│ ├────────────────────────────────────────────┤  flashes on   │
│ │ Consolidate observability         [in_review]│  34.0   SignalR│
│ ├────────────────────────────────────────────┤          push │
│ │ RAG index Hermes docs             [approved] │  22.0         │
│ └────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## 6. Runtime Architecture

```
┌────────────┐  OAuth2/OIDC/JWT   ┌────────────────┐  gRPC (Tonic)   ┌────────────────┐
│  React/TS  │ ─────────────────▶ │   FastAPI WES  │ ───────────────▶│  Rust Engine   │
│  Frontend  │ ◀───REST/JSON───── │      API       │ ◀──score────────│ Axum + Tonic   │
└─────┬──────┘                    └───────┬────────┘                 └────────────────┘
      │  WS (local) /                     │  publish
      │  Azure SignalR (prod)             ▼
      │                         ┌────────────────────┐
      └────────live push─────── │ Azure Event Hubs    │
                                 │ (native + Kafka-    │
                                 │  compatible :9093)  │
                                 └──────────┬──────────┘
                                            │
                                 ┌──────────▼──────────┐
                                 │ RAG: Azure AI Search │
                                 │ + HelixDB + TensorZero│
                                 └──────────────────────┘
```

## 7. Cloud-Portable Fallback Matrix

| Azure service | Production adapter | Local/offline fallback | Selected by |
|---|---|---|---|
| Entra ID | RS256 + tenant JWKS | HS256 dev-signed token | same code path, `security.py` |
| Event Hubs | `EventHubPublisher` (AMQP) | `InMemoryPublisher` | `WES_EVENTHUB_CONNECTION_STR` set/unset |
| Event Hubs (Kafka mode) | `KafkaCompatiblePublisher` (aiokafka → :9093) | n/a (opt-in) | explicit instantiation |
| SignalR Service | `AzureSignalRBroadcaster` (REST + JWT) | `LocalWebSocketHub` | `WES_SIGNALR_CONNECTION_STR` set/unset |
| Azure AI Search + HelixDB | adapter seam (`RetrievalGateway` protocol) | `InMemoryHybridGateway` | `get_retrieval_gateway()` |
| Rust risk engine | live gRPC call | Python-identical heuristic fallback | `RustEngineClient` try/except |

This matrix is itself the interview talking point: every Azure
integration is demonstrated as working code with an explicit, tested
seam — not asserted, not mocked away.

## 8. Language/Technology Nuances & Why

- **Rust dual-protocol (Axum *and* Tonic), one scoring core** —
  avoids duplicating business rules across HTTP and gRPC surfaces;
  `risk.rs` is unit-tested once and consumed by both.
- **Python fallback heuristic mirrors the Rust formula bit-for-bit** —
  an explicit design choice so a Rust-engine outage never produces
  divergent business behavior, only degraded latency.
- **React Query vs. Zustand boundary is deliberate**: anything that
  originates from the server (Workstream list) lives in the React
  Query cache and is mutated via SignalR push (`setQueryData`);
  anything UI-local (active filter, flash animation) lives in Zustand.
  This is precisely the seam KR's JD frames as "supporting the
  migration from legacy Apollo and Redux patterns."
- **Event Hubs, not a separate Kafka cluster** — one Azure PaaS
  resource serves both AMQP-native and Kafka-protocol consumers,
  directly enabling the JD's AWS→Azure consolidation goal without a
  parallel-running message bus during migration.
- **SignalR serverless mode** — keeps API pods stateless so AKS
  horizontal scaling isn't constrained by sticky WebSocket sessions.
- **`.proto` as single source of truth** — `tonic-build` (Rust) and
  `grpc_tools.protoc` (Python) both generate from `risk.proto`, so the
  contract can never silently drift between the two language runtimes.
