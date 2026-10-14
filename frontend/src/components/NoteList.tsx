import { noteFileUrl, type Note } from "../services/api";
import { StoredFiles } from "./StoredFiles";

export function NoteList({
  notes,
  onEdit,
  onDelete,
  onRemoveFile,
}: {
  notes: Note[];
  onEdit: (note: Note) => void;
  onDelete: (id: number) => void;
  onRemoveFile: (noteId: number, fileId: number) => void;
}) {
  return (
    <ul className="notes">
      {notes.map((note) => (
        <li key={note.id} className="note">
          <h2>{note.title}</h2>
          {note.tags.length ? <p className="tags">{note.tags.map((tag) => `#${tag}`).join(" ")}</p> : null}
          {note.content ? <p>{note.content}</p> : null}
          <StoredFiles
            files={note.files}
            href={(id) => noteFileUrl(note.id, id)}
            action="Remove"
            onAction={(id) => onRemoveFile(note.id, id)}
          />
          <div className="actions">
            <button type="button" className="ghost" onClick={() => onEdit(note)}>
              Edit
            </button>
            <button type="button" className="ghost" onClick={() => onDelete(note.id)}>
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
