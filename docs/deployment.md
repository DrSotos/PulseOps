# PulseOps Deployment Guide

## Docker Compose Production Deployment

The project provides a complete multi-container setup in `docker-compose.yml`:

```bash
# Start all containers in detached mode
docker compose up -d --build

# Run migrations inside the backend container
docker compose exec backend alembic upgrade head
```

### Services Deployed
1. `postgres`: PostgreSQL 16 Alpine with persistent volume `pgdata`.
2. `redis`: Redis 7 Alpine for coordination and caching.
3. `backend`: FastAPI REST API on port `8000`.
4. `worker`: Asynchronous monitoring engine running `python -m app.workers.scheduler`.
5. `frontend`: Production Nginx serving the React SPA bundle on port `3000`.

## Local Development Setup

### 1. Database & Cache
```bash
docker compose -f docker-compose.dev.yml up -d
```

### 2. Backend API
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Monitoring Worker
```bash
cd backend
python -m app.workers.scheduler
```

### 4. Frontend SPA
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 1-Click Free Cloud Deployment (Render / Railway)

### Option A: Render (Zero Configuration via Blueprint)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository: `https://github.com/DrSotos/PulseOps`.
4. Render reads `render.yaml` and will automatically provision:
   - Free Managed PostgreSQL Database
   - Unified Web Service running the Dockerfile (React Frontend + FastAPI API + In-Process Worker)
   - Free HTTPS/SSL certificate
5. Click **Apply** and wait 2-3 minutes for the build to finish. Your public URL will be ready at `https://pulseops-xxxx.onrender.com`.

### Option B: Railway
1. Log in to [Railway](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo** -> `DrSotos/PulseOps`.
3. Add a PostgreSQL database to the project (`+ New` -> `Database` -> `Add PostgreSQL`).
4. Railway will automatically link variables and deploy your Dockerfile with live public URL.


