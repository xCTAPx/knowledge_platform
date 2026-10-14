"""standalone files"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"


def upgrade():
    op.add_column("note_files", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE note_files
        SET user_id = notes.user_id
        FROM notes
        WHERE notes.id = note_files.note_id
        """
    )
    op.alter_column("note_files", "user_id", nullable=False)
    op.create_index("ix_note_files_user_id", "note_files", ["user_id"])
    op.create_foreign_key("note_files_user_id_fkey", "note_files", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("note_files_note_id_fkey", "note_files", type_="foreignkey")
    op.alter_column("note_files", "note_id", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key("note_files_note_id_fkey", "note_files", "notes", ["note_id"], ["id"], ondelete="SET NULL")


def downgrade():
    op.execute("DELETE FROM note_files WHERE note_id IS NULL")
    op.drop_constraint("note_files_note_id_fkey", "note_files", type_="foreignkey")
    op.alter_column("note_files", "note_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("note_files_note_id_fkey", "note_files", "notes", ["note_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("note_files_user_id_fkey", "note_files", type_="foreignkey")
    op.drop_index("ix_note_files_user_id", table_name="note_files")
    op.drop_column("note_files", "user_id")
