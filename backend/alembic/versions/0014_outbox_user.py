"""user id on delete outbox rows"""
import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"


def upgrade():
    op.add_column("outbox", sa.Column("user_id", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("outbox", "user_id")
