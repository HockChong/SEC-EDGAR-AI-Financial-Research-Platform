"""Explicit migrations; credentials come from validated process configuration."""

from alembic import context

from sec_research.adapters.postgres.database import create_database_engine
from sec_research.settings import load_settings


def run_migrations() -> None:
    if context.is_offline_mode():
        # Offline SQL rendering needs no credential or live connection.
        context.configure(dialect_name="postgresql", literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_database_engine(load_settings())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
