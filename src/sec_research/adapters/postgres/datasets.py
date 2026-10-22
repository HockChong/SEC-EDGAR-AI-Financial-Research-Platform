"""One PostgreSQL transaction exposes a complete Silver/Gold pair and projections."""

from collections.abc import Callable

from sqlalchemy import Connection, Engine, text

from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.contracts.canonical import canonical_bytes
from sec_research.contracts.datasets import DatasetError, Snapshot
from sec_research.processing.datasets import load_snapshot, verify_snapshot


class DatasetCatalog:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def active(self) -> str | None:
        with self.engine.connect() as connection:
            value = connection.execute(
                text("SELECT snapshot_id FROM dataset_active WHERE singleton")
            ).scalar_one()
            return str(value) if value is not None else None

    def activate(
        self,
        store: LocalDatasets,
        snapshot_id: str,
        *,
        expected_active: str | None,
        after_projection: Callable[[], None] | None = None,
    ) -> Snapshot:
        """CAS prevents stale builders replacing a newer snapshot. Also implements rollback."""
        snapshot = load_snapshot(store, snapshot_id)
        verify_snapshot(store, snapshot)
        with self.engine.begin() as connection:
            current = connection.execute(
                text("SELECT snapshot_id FROM dataset_active WHERE singleton FOR UPDATE")
            ).scalar_one()
            if current != expected_active:
                raise DatasetError("active_snapshot_conflict")
            existing = connection.execute(
                text("SELECT manifest FROM dataset_snapshots WHERE id = :id"), {"id": snapshot.id}
            ).scalar_one_or_none()
            manifest = snapshot.model_dump(mode="json")
            if existing is not None and existing != manifest:
                raise DatasetError("catalog_manifest_conflict")
            connection.execute(
                text("""
                INSERT INTO dataset_snapshots(id, dataset_version, manifest)
                VALUES (:id, :version, CAST(:manifest AS jsonb)) ON CONFLICT (id) DO NOTHING
            """),
                {
                    "id": snapshot.id,
                    "version": snapshot.silver.dataset_version,
                    "manifest": canonical_bytes(manifest).decode(),
                },
            )
            self._project(connection, store, snapshot)
            if after_projection is not None:
                after_projection()
            if current != snapshot.id:
                connection.execute(
                    text("UPDATE dataset_active SET snapshot_id = :id WHERE singleton"),
                    {"id": snapshot.id},
                )
                connection.execute(
                    text("""
                    INSERT INTO dataset_activation_events(previous_id, snapshot_id)
                    VALUES (:previous, :id)
                """),
                    {"previous": current, "id": snapshot.id},
                )
        return snapshot

    def _project(self, connection: Connection, store: LocalDatasets, snapshot: Snapshot) -> None:
        # Projections are derived. Rebuild transactionally, including a damaged old projection.
        connection.execute(
            text("DELETE FROM dataset_projections WHERE snapshot_id = :id"), {"id": snapshot.id}
        )
        statement = text("""
            INSERT INTO dataset_projections(snapshot_id, dataset, record_id, record)
            VALUES (:snapshot, :dataset, :id, CAST(:record AS jsonb))
        """)
        count = 0
        for item in snapshot.gold.objects:
            records = store.read(item)
            for start in range(0, len(records), 256):
                batch = records[start : start + 256]
                connection.execute(
                    statement,
                    [
                        {
                            "snapshot": snapshot.id,
                            "dataset": item.dataset,
                            "id": row.id,
                            "record": canonical_bytes(row.model_dump(mode="json")).decode(),
                        }
                        for row in batch
                    ],
                )
                count += len(batch)
        stored = connection.execute(
            text("SELECT count(*) FROM dataset_projections WHERE snapshot_id = :id"),
            {"id": snapshot.id},
        ).scalar_one()
        if stored != count:
            raise DatasetError("incomplete_serving_projection")
