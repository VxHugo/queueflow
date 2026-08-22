# Architecture decisions

## ADR-001: PostgreSQL owns durable state

Jobs, attempts, workers and audit events are written to PostgreSQL before they are exposed as completed work. Redis is intentionally not the system of record.

## ADR-002: Transactional outbox bridges database and queue

Creating a job will write its outbox event in the same transaction. A dispatcher publishes pending events to Redis Streams and records publication only after Redis accepts them.

## ADR-003: One deployable Python codebase

The API and background roles share models, configuration and observability tooling, but run as separate Compose services. This avoids duplicated packages and keeps the operational boundaries visible.

