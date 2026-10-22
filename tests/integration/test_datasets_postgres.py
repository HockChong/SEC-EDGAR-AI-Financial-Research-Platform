from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import text

from sec_research.adapters.postgres.database import create_database_engine
from sec_research.adapters.postgres.datasets import DatasetCatalog
from sec_research.contracts.datasets import DatasetError
from sec_research.processing.datasets import build_snapshot
from sec_research.settings import Settings
from tests.dataset_helpers import dataset_inputs
from tests.integration.test_database import migration_config

pytestmark = pytest.mark.integration


def test_publication_failure_replay_rollback_and_rebuild(
    database_settings: Settings,
    tmp_path: Path,
) -> None:
    command.upgrade(migration_config(), "head")
    engine = create_database_engine(database_settings)
    try:
        catalog = DatasetCatalog(engine)
        bronze, store, fetches, spec = dataset_inputs(tmp_path)
        first = build_snapshot(bronze, store, fetches, spec)
        second = build_snapshot(
            bronze, store, fetches, spec.model_copy(update={"code_revision": "second"})
        )
        assert first.id is not None and second.id is not None
        assert catalog.active() is None

        def interrupt() -> None:
            # Separate connection cannot see uncommitted projections or activation.
            assert DatasetCatalog(engine).active() == first.id
            raise RuntimeError("simulated process failure")

        catalog.activate(store, first.id, expected_active=None)
        with pytest.raises(RuntimeError, match="simulated"):
            catalog.activate(store, second.id, expected_active=first.id, after_projection=interrupt)
        assert catalog.active() == first.id
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM dataset_snapshots WHERE id = :id"), {"id": second.id}
                ).scalar_one()
                == 0
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM dataset_projections WHERE snapshot_id = :id"),
                    {"id": second.id},
                ).scalar_one()
                == 0
            )
        catalog.activate(store, second.id, expected_active=first.id)
        with pytest.raises(DatasetError, match="active_snapshot_conflict"):
            catalog.activate(store, first.id, expected_active=first.id)
        # Explicit rollback and same-version rerun preserve immutable snapshots.
        catalog.activate(store, first.id, expected_active=second.id)
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM dataset_projections WHERE snapshot_id = :id"), {"id": first.id}
            )
        catalog.activate(store, first.id, expected_active=first.id)
        assert DatasetCatalog(engine).active() == first.id
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM dataset_activation_events")
                ).scalar_one()
                == 3
            )
            count = connection.execute(
                text("SELECT count(*) FROM dataset_projections WHERE snapshot_id = :id"),
                {"id": first.id},
            ).scalar_one()
            assert count == sum(i.row_count for i in first.gold.objects)
        # Corrupt artifacts cannot replace the current activation.
        store.path(second.gold.objects[0].path).write_bytes(b"corrupt")
        with pytest.raises(DatasetError, match="checksum"):
            catalog.activate(store, second.id, expected_active=first.id)
        assert catalog.active() == first.id
    finally:
        engine.dispose()
