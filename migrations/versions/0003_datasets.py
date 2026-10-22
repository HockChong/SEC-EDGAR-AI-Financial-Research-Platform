"""Atomic dataset activation and rebuildable serving projections."""

from alembic import op

revision = "0003_datasets"
down_revision = "0002_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE dataset_snapshots (
            id text PRIMARY KEY, dataset_version text NOT NULL UNIQUE,
            manifest jsonb NOT NULL, registered_at timestamptz NOT NULL DEFAULT clock_timestamp()
        );
        CREATE TABLE dataset_active (
            singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
            snapshot_id text REFERENCES dataset_snapshots(id)
        );
        INSERT INTO dataset_active(singleton) VALUES (true);
        CREATE TABLE dataset_projections (
            snapshot_id text NOT NULL REFERENCES dataset_snapshots(id),
            dataset text NOT NULL, record_id text NOT NULL, record jsonb NOT NULL,
            PRIMARY KEY (snapshot_id, dataset, record_id)
        );
        CREATE TABLE dataset_activation_events (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            previous_id text REFERENCES dataset_snapshots(id),
            snapshot_id text NOT NULL REFERENCES dataset_snapshots(id),
            activated_at timestamptz NOT NULL DEFAULT clock_timestamp()
        );
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE dataset_activation_events;
        DROP TABLE dataset_projections;
        DROP TABLE dataset_active;
        DROP TABLE dataset_snapshots;
    """)
