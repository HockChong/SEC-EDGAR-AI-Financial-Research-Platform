"""Append-only Bronze provenance and recoverable source work records."""

from alembic import op

revision = "0002_ingestion"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE ingestion_runs (
            id uuid PRIMARY KEY, started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            finished_at timestamptz, status text NOT NULL CHECK
                (status IN ('running', 'succeeded', 'failed')),
            config jsonb NOT NULL, pipeline_version text NOT NULL DEFAULT 'bronze-1'
        );
        CREATE TABLE ingestion_sources (
            url text PRIMARY KEY, metadata jsonb NOT NULL,
            status text NOT NULL CHECK
                (status IN ('downloading', 'succeeded', 'failed', 'quarantined')),
            attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
            error_code text, updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
        );
        CREATE TABLE ingestion_fetches (
            id uuid PRIMARY KEY, run_id uuid NOT NULL REFERENCES ingestion_runs(id),
            source_url text NOT NULL REFERENCES ingestion_sources(url),
            fetched_at timestamptz NOT NULL, sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            record jsonb NOT NULL
        );
        CREATE INDEX ingestion_fetch_source ON ingestion_fetches(source_url, fetched_at DESC);
        CREATE TABLE ingestion_attempts (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            run_id uuid NOT NULL REFERENCES ingestion_runs(id),
            source_url text NOT NULL REFERENCES ingestion_sources(url),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            status text NOT NULL, error_code text, retryable boolean NOT NULL,
            http_attempts integer NOT NULL CHECK (http_attempts >= 0)
        );
        CREATE TABLE sec_rate_limit (
            singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
            next_request timestamptz NOT NULL DEFAULT '-infinity'
        );
        INSERT INTO sec_rate_limit (singleton) VALUES (true);
        CREATE FUNCTION protect_ingestion_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'ingestion history is append-only'; END $$;
        CREATE TRIGGER immutable_fetches BEFORE UPDATE OR DELETE ON ingestion_fetches
            FOR EACH ROW EXECUTE FUNCTION protect_ingestion_history();
        CREATE TRIGGER immutable_attempts BEFORE UPDATE OR DELETE ON ingestion_attempts
            FOR EACH ROW EXECUTE FUNCTION protect_ingestion_history();
    """)


def downgrade() -> None:
    # Never discard provenance as an implicit rollback side effect.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM ingestion_sources) OR EXISTS (SELECT 1 FROM ingestion_runs)
            THEN RAISE EXCEPTION 'nonempty ingestion history requires an explicit backup/migration';
            END IF;
        END $$;
        DROP TABLE ingestion_attempts, ingestion_fetches, ingestion_sources, ingestion_runs,
            sec_rate_limit;
        DROP FUNCTION protect_ingestion_history();
    """)
