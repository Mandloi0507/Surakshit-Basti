"""add_habitation_phase5_scoring_fields

Revision ID: 1f6d35b58c2a
Revises: ca8fb6b1c71e
Create Date: 2026-10-08 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1f6d35b58c2a"
down_revision: Union[str, Sequence[str], None] = "ca8fb6b1c71e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store vulnerability and urgency explanation terms on habitations."""
    op.add_column("habitations", sa.Column("structural_hazard", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("habitations", sa.Column("time_factor", sa.Float(), server_default="1.0", nullable=False))
    op.add_column("habitations", sa.Column("raw_urgency_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("habitations", sa.Column("vulnerability_breakdown_json", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False))
    op.add_column("habitations", sa.Column("urgency_breakdown_json", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False))
    op.alter_column("habitations", "structural_hazard", server_default=None)
    op.alter_column("habitations", "time_factor", server_default=None)
    op.alter_column("habitations", "raw_urgency_score", server_default=None)
    op.alter_column("habitations", "vulnerability_breakdown_json", server_default=None)
    op.alter_column("habitations", "urgency_breakdown_json", server_default=None)


def downgrade() -> None:
    """Remove phase 5 habitation scoring fields."""
    op.drop_column("habitations", "urgency_breakdown_json")
    op.drop_column("habitations", "vulnerability_breakdown_json")
    op.drop_column("habitations", "raw_urgency_score")
    op.drop_column("habitations", "time_factor")
    op.drop_column("habitations", "structural_hazard")
