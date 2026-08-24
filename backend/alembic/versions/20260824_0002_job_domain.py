"""Create the QueueFlow job domain tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260824_0002"
down_revision = "20260821_0001"
branch_labels = None
depends_on = None

jsonb = postgresql.JSONB(astext_type=sa.Text())
uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("queue_name", sa.String(100), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("payload", jsonb, nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(255)),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", jsonb), sa.Column("last_error", jsonb),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("backoff_base", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("backoff_max", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)), sa.Column("available_at", sa.DateTime(timezone=True)),
        sa.Column("lease_owner", sa.String(100)), sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="ck_jobs_progress"),
        sa.CheckConstraint("attempts >= 0 AND max_attempts > 0", name="ck_jobs_attempts"),
        sa.CheckConstraint("backoff_base > 0 AND backoff_max >= backoff_base", name="ck_jobs_backoff"),
        sa.CheckConstraint("status IN ('SCHEDULED','QUEUED','RUNNING','RETRYING','SUCCEEDED','FAILED','DEAD_LETTERED','CANCELED')", name="ck_jobs_status"),
        sa.CheckConstraint("priority IN ('CRITICAL','HIGH','NORMAL','LOW')", name="ck_jobs_priority"),
        sa.UniqueConstraint("queue_name", "idempotency_key", name="uq_jobs_queue_idempotency_key"),
    )
    for name, columns in (("ix_jobs_status_priority", ["status", "priority"]), ("ix_jobs_available_at", ["available_at"]), ("ix_jobs_scheduled_at", ["scheduled_at"]), ("ix_jobs_lease_expires_at", ["lease_expires_at"]), ("ix_jobs_created_at", ["created_at"])):
        op.create_index(name, "jobs", columns)
    op.create_table("job_attempts", sa.Column("id", uuid, primary_key=True), sa.Column("job_id", uuid, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False), sa.Column("worker_id", sa.String(100)), sa.Column("status", sa.String(20), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("finished_at", sa.DateTime(timezone=True)), sa.Column("duration_ms", sa.Integer()), sa.Column("error_type", sa.String(255)), sa.Column("error_message", sa.Text()), sa.Column("error_stack", sa.Text()), sa.Column("result", jsonb), sa.UniqueConstraint("job_id", "attempt_number", name="uq_attempt_job_number"))
    op.create_index("ix_attempts_worker_id", "job_attempts", ["worker_id"])
    op.create_table("workers", sa.Column("id", sa.String(100), primary_key=True), sa.Column("name", sa.String(100), nullable=False, unique=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("hostname", sa.String(255), nullable=False), sa.Column("capacity", sa.Integer(), nullable=False), sa.Column("active_jobs", sa.Integer(), nullable=False, server_default="0"), sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("version", sa.String(50), nullable=False), sa.Column("metadata", jsonb, nullable=False, server_default="{}"))
    op.create_table("job_events", sa.Column("id", uuid, primary_key=True), sa.Column("job_id", uuid, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("metadata", jsonb, nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("outbox_events", sa.Column("id", uuid, primary_key=True), sa.Column("aggregate_id", uuid, nullable=False), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("payload", jsonb, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("publish_attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("last_error", sa.Text()))
    op.create_index("ix_outbox_unpublished", "outbox_events", ["published_at", "created_at"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("job_events")
    op.drop_table("workers")
    op.drop_table("job_attempts")
    op.drop_table("jobs")
