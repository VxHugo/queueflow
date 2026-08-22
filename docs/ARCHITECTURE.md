# Architecture

The system uses PostgreSQL as its durable source of truth. Redis Streams carries job commands from a transactional outbox to worker consumer groups. Redis Pub/Sub will later carry ephemeral dashboard updates while important events remain durable in PostgreSQL.

```text
Dashboard -> FastAPI -> PostgreSQL <- Scheduler / Workers
                    -> Outbox -> Dispatcher -> Redis Streams -> Workers
```

The backend is one Python package with separate commands for the API, dispatcher, scheduler and workers. This keeps shared domain rules in one place while Docker Compose runs each role independently.

Delivery is at-least-once: a worker lease can expire and a job can be delivered again. Handlers must therefore make result persistence idempotent; QueueFlow does not claim exactly-once processing.

