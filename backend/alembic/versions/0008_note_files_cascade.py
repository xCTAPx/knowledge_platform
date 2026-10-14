"""delete note files with note"""
from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade():
    op.drop_constraint("note_files_note_id_fkey", "note_files", type_="foreignkey")
    op.create_foreign_key("note_files_note_id_fkey", "note_files", "notes", ["note_id"], ["id"], ondelete="CASCADE")


def downgrade():
    op.drop_constraint("note_files_note_id_fkey", "note_files", type_="foreignkey")
    op.create_foreign_key("note_files_note_id_fkey", "note_files", "notes", ["note_id"], ["id"], ondelete="SET NULL")
