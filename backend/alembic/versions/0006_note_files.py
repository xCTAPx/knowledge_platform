"""note files"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.create_table(
        "note_files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("stored", sa.String(80), nullable=False, unique=True),
    )
    op.create_index("ix_note_files_note_id", "note_files", ["note_id"])


def downgrade():
    op.drop_index("ix_note_files_note_id", table_name="note_files")
    op.drop_table("note_files")
