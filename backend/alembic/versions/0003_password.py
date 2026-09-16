"""add user password hash"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002_users_only"


def upgrade():
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(255), nullable=False, server_default=""),
    )
    op.alter_column("users", "hashed_password", server_default=None)


def downgrade():
    op.drop_column("users", "hashed_password")
