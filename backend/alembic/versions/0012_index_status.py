"""index status for notes and files"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"


def upgrade():
    op.add_column("notes", sa.Column("index_status", sa.String(16), nullable=False, server_default="ready"))
    op.add_column("notes", sa.Column("index_gen", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("file", sa.Column("index_status", sa.String(16), nullable=False, server_default="ready"))
    op.alter_column("notes", "index_status", server_default="pending")
    op.alter_column("file", "index_status", server_default="pending")


def downgrade():
    op.drop_column("file", "index_status")
    op.drop_column("notes", "index_gen")
    op.drop_column("notes", "index_status")
