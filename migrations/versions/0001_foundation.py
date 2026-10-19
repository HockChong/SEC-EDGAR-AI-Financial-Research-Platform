"""Enable pgvector without introducing later-phase application tables."""

from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector VERSION '0.8.1'")


def downgrade() -> None:
    # Extension lifecycle belongs to the database administrator. Never cascade-delete user vectors.
    pass
