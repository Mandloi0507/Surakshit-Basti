"""add_structural_hazard_to_cells

Revision ID: ca8fb6b1c71e
Revises: 8fc2b09eb97c
Create Date: 2026-10-08 01:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ca8fb6b1c71e"
down_revision: Union[str, Sequence[str], None] = "8fc2b09eb97c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store structural hazard separately from rainfall-driven dynamic hazard."""
    op.add_column(
        "cells",
        sa.Column("structural_hazard", sa.Float(), server_default="0.0", nullable=False),
    )
    op.create_index(
        op.f("ix_cells_structural_hazard"),
        "cells",
        ["structural_hazard"],
        unique=False,
    )
    op.alter_column("cells", "structural_hazard", server_default=None)


def downgrade() -> None:
    """Remove structural hazard storage."""
    op.drop_index(op.f("ix_cells_structural_hazard"), table_name="cells")
    op.drop_column("cells", "structural_hazard")
