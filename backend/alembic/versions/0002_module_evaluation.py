"""Persist module-specific evaluated safeguard criteria independently of core cases."""
from alembic import op
import sqlalchemy as sa

revision = "0002_module_evaluation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # A server default backfills already-existing synthetic/prototype evaluations.
    op.add_column("evaluations", sa.Column("criteria", sa.JSON, nullable=False, server_default=sa.text("'[]'")))


def downgrade():
    op.drop_column("evaluations", "criteria")
