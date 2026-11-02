# PulseOps System Architecture

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Presentation Tier"]
        FE["React + TypeScript SPA\n(Vite, Tailwind, Recharts)"]
    end

    subgraph BackendTier["Application Tier"]
        API["FastAPI REST API Server\n(/api/v1)"]
        SSE["SSE Broker (EventManager)\n(Real-time push)"]
        SEC["SSRF Security Shield\n(DNS & IP validation)"]
    end

    subgraph WorkerTier["Worker Tier"]
        SCHED["Monitoring Worker Engine\n(Independent Async Process)"]
        PROBE["HTTPX Async Prober\n(Monotonic timing)"]
        INC["Incident Detection Engine\n(State machine & Deduplication)"]
        NOTIF["Notification Dispatcher\n(SMTP & Webhooks)"]
    end

    subgraph DataTier["Data Persistence Tier"]
        PG[("PostgreSQL 16\n(SQLAlchemy Async + Alembic)")]
    end

    FE -->|REST API Requests| API
    FE <--|Live SSE Updates| SSE
    API --> SEC
    API --> PG
    SCHED --> PROBE
    PROBE -->|Persist Checks| PG
    PROBE --> INC
    INC -->|Open/Resolve Incidents| PG
    INC --> NOTIF
    NOTIF -->|Audit Logs| PG
    INC -->|Push Events| SSE
```

## Architectural Components

1. **Frontend (React 18 + TypeScript + Vite)**:
   - Modern dark-themed dashboard.
   - Real-time updates delivered through Server-Sent Events (SSE).
   - Dynamic latency percentile distribution charts ($P_{50}, P_{90}, P_{95}, P_{99}$).

2. **FastAPI REST Backend (`/api/v1`)**:
   - Asynchronous endpoints with Pydantic v2 validation.
   - JWT token authentication with bcrypt password hashing.
   - Comprehensive error handling and CORS support.

3. **Monitoring Worker (`app.workers.scheduler`)**:
   - Decoupled process running independently of browser sessions.
   - Concurrency bounded by async semaphores (`MAX_CONCURRENT_CHECKS`).
   - Monotonic microsecond clock for accurate latency metrics.

4. **Incident Engine (`app.services.incidents.detector`)**:
   - Evaluates consecutive probe failures to prevent flapping.
   - Incident deduplication (one active ticket per endpoint per issue).
   - Automated ticket recovery on consecutive verified successes.

