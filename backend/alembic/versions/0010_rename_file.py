"""rename note_files to file"""
from alembic import op

revision = "0010"
down_revision = "0009"


def upgrade():
    op.rename_table("note_files", "file")
    op.execute("ALTER INDEX ix_note_files_note_id RENAME TO ix_file_note_id")
    op.execute("ALTER INDEX ix_note_files_user_id RENAME TO ix_file_user_id")
    for old, new in [
        ("note_files_pkey", "file_pkey"),
        ("note_files_stored_key", "file_stored_key"),
        ("note_files_note_id_fkey", "file_note_id_fkey"),
        ("note_files_user_id_fkey", "file_user_id_fkey"),
        ("note_files_created_at_not_null", "file_created_at_not_null"),
        ("note_files_id_not_null", "file_id_not_null"),
        ("note_files_name_not_null", "file_name_not_null"),
        ("note_files_stored_not_null", "file_stored_not_null"),
        ("note_files_user_id_not_null", "file_user_id_not_null"),
    ]:
        op.execute(f"ALTER TABLE file RENAME CONSTRAINT {old} TO {new}")


def downgrade():
    for old, new in [
        ("file_user_id_not_null", "note_files_user_id_not_null"),
        ("file_stored_not_null", "note_files_stored_not_null"),
        ("file_name_not_null", "note_files_name_not_null"),
        ("file_id_not_null", "note_files_id_not_null"),
        ("file_created_at_not_null", "note_files_created_at_not_null"),
        ("file_user_id_fkey", "note_files_user_id_fkey"),
        ("file_note_id_fkey", "note_files_note_id_fkey"),
        ("file_stored_key", "note_files_stored_key"),
        ("file_pkey", "note_files_pkey"),
    ]:
        op.execute(f"ALTER TABLE file RENAME CONSTRAINT {old} TO {new}")
    op.execute("ALTER INDEX ix_file_user_id RENAME TO ix_note_files_user_id")
    op.execute("ALTER INDEX ix_file_note_id RENAME TO ix_note_files_note_id")
    op.rename_table("file", "note_files")
