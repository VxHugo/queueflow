# QueueFlow

**Project status: Core platform**

QueueFlow is a distributed background-job platform built to make queue processing observable and explainable. The final product will combine PostgreSQL-backed job state, Redis Streams delivery, independently deployable workers and a real-time React dashboard.

## Foundation delivered

- FastAPI service with OpenAPI documentation and liveness/readiness endpoints.
- Readiness checks that use PostgreSQL and Redis instead of fabricated status.
- Docker Compose services for PostgreSQL, Redis, the API and the dashboard shell.
- React, TypeScript and Tailwind dashboard foundation.
- Alembic initialized for the persistent domain introduced in the next milestone.
- Durable job, attempt, worker, event and outbox schema with lifecycle rules and idempotency support.
- Initial CI for backend lint/tests and frontend production builds.

## Local development

Copy `.env.example` to `.env`, then run:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`; its OpenAPI UI is at `http://localhost:8000/docs`. The dashboard is available at `http://localhost:5173`.

## Checks

```bash
docker compose run --rm api ruff check .
docker compose run --rm api pytest
npm --prefix frontend run build
```

## Architecture and roadmap

See [architecture](docs/ARCHITECTURE.md), [recorded decisions](docs/DECISIONS.md), and the [seven-day roadmap](docs/ROADMAP.md). QueueFlow uses at-least-once delivery; idempotency will be implemented at the API and handler layers in later milestones.

