"""when an outbox row was sent to Redis"""
import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"


def upgrade():
    op.add_column("outbox", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("outbox", "published_at")
