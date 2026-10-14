"""rename accuracy_pct to fidelity_pct, drop memory_usage_mb, add ONNX baseline format

Revision ID: b7e41c2a9d10
Revises: 933d9c7c6103
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e41c2a9d10"
down_revision: Union[str, None] = "933d9c7c6103"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("benchmarks") as batch:
        batch.alter_column("accuracy_pct", new_column_name="fidelity_pct")
        batch.drop_column("memory_usage_mb")

    # SQLite stores enums as plain strings; only PostgreSQL has a real enum type to extend.
    if op.get_bind().dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE targetformat ADD VALUE IF NOT EXISTS 'ONNX'")


def downgrade() -> None:
    with op.batch_alter_table("benchmarks") as batch:
        batch.alter_column("fidelity_pct", new_column_name="accuracy_pct")
        batch.add_column(sa.Column("memory_usage_mb", sa.Float(), nullable=True))
