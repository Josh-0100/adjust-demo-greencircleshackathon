"""Initial relational schema: resources, review cases, audit, evaluation and progress.

This revision uses portable SQLAlchemy types and explicit migration operations.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("resources",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("title", sa.String(180), nullable=False),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("module_id", sa.String(80), nullable=False),
        sa.Column("borough", sa.String(80), nullable=False), sa.Column("description", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False), sa.Column("source_label", sa.String(180), nullable=False),
        sa.Column("source_url", sa.String(1000)), sa.Column("synthetic", sa.Boolean, nullable=False),
        sa.Column("approved", sa.Boolean, nullable=False), sa.Column("seed_record", sa.Boolean, nullable=False),
        sa.Column("skills", sa.JSON, nullable=False), sa.Column("next_steps", sa.JSON, nullable=False))
    op.create_index("ix_resources_module_id", "resources", ["module_id"])
    op.create_index("ix_resources_borough", "resources", ["borough"])
    op.create_table("cases",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("reference", sa.String(40), nullable=False),
        sa.Column("resident_name", sa.String(100), nullable=False), sa.Column("message", sa.Text, nullable=False),
        sa.Column("module_id", sa.String(80), nullable=False), sa.Column("borough", sa.String(80), nullable=False),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("department", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("review_note", sa.Text),
        sa.Column("analysis", sa.JSON, nullable=False), sa.Column("seed_record", sa.Boolean, nullable=False))
    op.create_index("ix_cases_reference", "cases", ["reference"], unique=True)
    op.create_index("ix_cases_module_id", "cases", ["module_id"])
    op.create_index("ix_cases_borough", "cases", ["borough"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_table("audit_events",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(30), nullable=False), sa.Column("entity", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("detail", sa.Text, nullable=False))
    op.create_table("evaluations",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("processing_ms", sa.Float, nullable=False), sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("source_count", sa.Integer, nullable=False), sa.Column("escalated", sa.Boolean, nullable=False),
        sa.Column("provider", sa.String(100), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_evaluations_case_id", "evaluations", ["case_id"])
    op.create_table("feedback",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id"))
    op.create_table("learning_progress",
        sa.Column("id", sa.Integer, primary_key=True), sa.Column("case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", sa.String(80), nullable=False), sa.Column("completed", sa.Boolean, nullable=False),
        sa.Column("note", sa.String(500), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "step_id", name="uq_learning_case_step"))
    op.create_index("ix_learning_progress_case_id", "learning_progress", ["case_id"])


def downgrade():
    for name in ["learning_progress", "feedback", "evaluations", "audit_events", "cases", "resources"]:
        op.drop_table(name)

