# PulseOps — API Monitoring & Incident Management Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-emerald.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=flat&logo=vercel)](https://pulse-595iem5r7-drsotos.vercel.app/)

**PulseOps** is a full-stack, production-grade API monitoring and incident management platform. It periodically tests HTTP/HTTPS endpoints, records sub-millisecond latency telemetry, calculates percentile distributions ($P_{50}, P_{90}, P_{95}, P_{99}$), manages incident lifecycles, dispatches email & webhook alerts, and streams real-time updates via Server-Sent Events (SSE).



---

## 1. Core Capabilities

- **Automated HTTP Probing**: Configurable intervals (30s to 15m), custom headers, POST payloads, expected HTTP status codes, and body content assertions.
- **Microsecond Monotonic Timing**: High-precision response time capture resilient against system wall-clock synchronization drift.
- **SSRF Guard**: Strict validation blocking loopback, link-local, RFC 1918 private ranges, and cloud metadata endpoints (`169.254.169.254`).
- **Incident State Engine**: Failure thresholds (default 3 consecutive fails), deduplication of active outages, severity ranking, and automated recovery on consecutive successes.
- **Multi-Channel Alerting**: SMTP email notifications with HTML severity styling and webhook delivery tracking with status logging and retries.
- **Real-Time Streaming**: Server-Sent Events (SSE) push probe results and incident status changes live to connected dashboard sessions.
- **Statistical Distributions**: Real-time calculations of Availability Uptime %, Mean Latency, Min, Max, and Percentiles ($P_{50}, P_{90}, P_{95}, P_{99}$).

---

## 2. Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy 2.0 (AsyncIO) with `asyncpg`
- **Migrations**: Alembic
- **HTTP Client**: HTTPX (Asynchronous with HTTP/2 support)
- **Security**: Bcrypt password hashing & PyJWT / Python-Jose
- **Testing**: Pytest, Pytest-AsyncIO, aiosqlite

### Frontend
- **Framework**: React 18 with TypeScript 5.7
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS (Dark SRE theme)
- **Charting**: Recharts
- **Icons**: Lucide React
- **Testing**: Vitest, React Testing Library, JSDOM

### Infrastructure
- **Database**: PostgreSQL 16
- **Cache / Message Queue**: Redis 7
- **Containerization**: Docker & Docker Compose

---

## 3. Project Structure

```text
pulseops/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application setup & router registration
│   │   ├── api/v1/
│   │   │   ├── deps.py                 # Auth and pagination dependencies
│   │   │   ├── routes/                 # auth, endpoints, incidents, notifications, dashboard, sse
│   │   │   └── schemas/                # Pydantic v2 schemas
│   │   ├── core/
│   │   │   ├── config.py               # Environment configuration
│   │   │   ├── logging.py              # Structured application logger
│   │   │   └── security.py             # Bcrypt and JWT token handling
│   │   ├── db/
│   │   │   ├── base.py                 # DeclarativeBase with naming conventions
│   │   │   └── session.py              # Async database engine & session maker
│   │   ├── models/                     # SQLAlchemy models: User, MonitoredEndpoint,
│   │   │                               # MonitoringCheck, Incident, IncidentEvent,
│   │   │                               # NotificationChannel, NotificationDelivery
│   │   ├── services/
│   │   │   ├── monitoring/             # HTTP checker & scheduler service
│   │   │   ├── incidents/              # Detector, deduplication & state machine
│   │   │   ├── notifications/          # Email, Webhook, and dispatch logic
│   │   │   ├── statistics/             # Latency, percentiles, uptime calculators
│   │   │   └── events.py               # In-memory SSE event bus
│   │   ├── utils/
│   │   │   └── url_validator.py        # SSRF mitigation logic
│   │   └── workers/
│   │       └── scheduler.py            # Standalone daemon monitoring worker
│   ├── migrations/                     # Alembic async migration environment
│   ├── tests/                          # 15+ automated pytest unit and integration tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/                 # StatusBadge, LatencyChart, Modal, Navbar, Sidebar
│   │   ├── contexts/                   # AuthContext with session restoration
│   │   ├── pages/                      # Dashboard, Endpoints, EndpointDetail, Incidents,
│   │   │                               # IncidentDetail, Notifications, Settings, Login, Register
│   │   ├── services/                   # REST API client & real-time SSE stream hook
│   │   ├── types/                      # TypeScript definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docs/                               # Architecture, API, Monitoring, Incident & Deployment guides
├── docker-compose.yml                  # Production multi-service compose
├── docker-compose.dev.yml              # Local development compose (Postgres + Redis)
├── Dockerfile                          # Multi-stage production container
├── render.yaml                         # Render Cloud Blueprint
├── vercel.json                         # Vercel SPA configuration
├── LICENSE                             # MIT License
└── README.md
```

---

## 4. Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+ (Node 20+ recommended)
- Docker & Docker Compose (optional for local containerized Postgres)

### Step 1: Clone & Configure
```bash
cd pulseops
cp backend/.env.example backend/.env
```

### Step 2: Start PostgreSQL & Redis
```bash
docker compose -f docker-compose.dev.yml up -d
```

### Step 3: Setup Backend
```bash
cd backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
```

### Step 4: Run the Services

**Terminal 1 — Backend API:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Monitoring Worker:**
```bash
cd backend
python -m app.workers.scheduler
```

**Terminal 3 — Frontend SPA:**
```bash
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:3000`** in your browser.
API documentation is available at **`http://localhost:8000/docs`**.

---

## 5. Running Automated Tests

### Backend Test Suite (Pytest)
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Test Suite (Vitest)
```bash
cd frontend
npm test
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 6. Docker Production Deployment

To run the complete stack including Frontend Nginx, Backend API, Monitoring Worker, and PostgreSQL:

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

---

## 7. Security Architecture

1. **SSRF Mitigation**:
   - Every target destination is resolved before request dispatch.
   - Prohibits IPv4/IPv6 loopback, link-local, private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata (`169.254.169.254`, `metadata.google.internal`).
   - Redirects are disabled by default to prevent open-redirect SSRF bypasses.
2. **Access Control**:
   - Passwords hashed using standard `bcrypt` with unique salts.
   - User ownership strictly enforced across all endpoint, incident, and channel operations.
3. **Defense in Depth**:
   - Response body reading is capped at 1MB to prevent memory exhaustion attacks.
   - Internal monitoring exceptions never expose raw stack traces in client responses.

---

## 8. Roadmap & Upcoming Features

- Distributed worker coordination via Celery / Redis Streams
- Multi-region geo-probes (US-East, EU-Central, AP-Southeast)
- SSL Certificate expiration alerts (warning at 30/14/7 days before expiry)
- Automated PagerDuty, Opsgenie, and Discord bot webhooks
- Custom JSONPath response assertion queries

---

## 9. Author & License

Developed by [DrSotos](https://github.com/DrSotos).

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

