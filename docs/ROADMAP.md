# QueueFlow roadmap

QueueFlow is developed in seven reviewable milestones. This repository is intentionally built one milestone per day.

1. **Foundation** — monorepo, runnable local infrastructure, health checks, initial dashboard shell and CI.
2. **Domain and persistence** — job state machine, database schema, repositories and idempotency.
3. **Queue and workers** — Redis Streams transport, dispatcher, heartbeats, leases and handlers.
4. **Reliability** — scheduling, retries, cancellation, dead-letter queue and recovery.
5. **API and observability** — complete REST API, real-time events, metrics and integration tests.
6. **Dashboard** — live operational views connected to the API.
7. **Demo and polish** — load testing, end-to-end demo, documentation and release validation.

