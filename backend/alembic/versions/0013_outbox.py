"""outbox for indexing jobs"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"


def upgrade():
    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("item_id", sa.Integer, nullable=False),
        sa.Column("gen", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_table("outbox")
