# QueueFlow roadmap

QueueFlow is delivered in four focused daily milestones. The original seven-day plan was consolidated by moving the dashboard foundation into Day 2 and grouping tightly coupled capabilities without reducing the required product scope.

1. **Foundation** — monorepo, runnable local infrastructure, health checks, initial dashboard shell and CI. Completed.
2. **Core platform and interface** — job domain, persistence, state machine, idempotency, outbox, dashboard information architecture and operations UI. In progress.
3. **Processing and reliability** — Redis Streams, dispatcher, three workers, handlers, priority scheduling, retries, cancellation, dead-letter queue, scheduling and recovery.
4. **Integration and demo** — complete REST API, WebSocket events, Prometheus, live dashboard integration, end-to-end tests, load test, demo assets and release validation.

Each milestone must still pass its related tests and CI before merge. The four-day cadence changes sequencing, not the expectation that the final dashboard is connected to real backend data.
