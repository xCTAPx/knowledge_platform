import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createNote,
  deleteNote,
  deleteNoteFile,
  getMe,
  listNotes,
  logout,
  noteFileUrl,
  updateNote,
  uploadNoteFile,
  type Note,
  type User,
} from "../services/api";

const FILE_OK = /\.(pdf|txt|md)$/i;

function tagsFrom(value: string) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [editing, setEditing] = useState<Note | null>(null);
  const [pending, setPending] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getMe()
      .then(async (me) => {
        setUser(me);
        setNotes(await listNotes());
      })
      .catch(() => setUser(null));
  }, []);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
    setNotes([]);
  }

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const title = String(data.get("title"));
    const tags = tagsFrom(String(data.get("tags") ?? ""));
    const content = String(data.get("content") ?? "");
    setError("");
    setBusy(true);
    setProgress(pending.length ? "Uploading files…" : "Saving…");
    const started = Date.now();
    try {
      let note = editing
        ? await updateNote(editing.id, title, tags, content)
        : await createNote(title, tags, content);
      const files = [...note.files];
      let i = 0;
      for (const file of pending) {
        i += 1;
        files.push(
          await uploadNoteFile(note.id, file, (pct) => {
            setProgress(`Uploading ${file.name} (${i}/${pending.length}) ${pct}%`);
          }),
        );
      }
      note = { ...note, files };
      setNotes(editing ? notes.map((item) => (item.id === note.id ? note : item)) : [note, ...notes]);
      setEditing(null);
      setPending([]);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save note");
    } finally {
      const wait = 600 - (Date.now() - started);
      if (wait > 0) await new Promise((resolve) => setTimeout(resolve, wait));
      setBusy(false);
      setProgress("");
    }
  }

  async function onDelete(id: number) {
    await deleteNote(id);
    setNotes(notes.filter((note) => note.id !== id));
    if (editing?.id === id) {
      setEditing(null);
      setPending([]);
    }
  }

  async function onRemoveFile(noteId: number, fileId: number) {
    await deleteNoteFile(noteId, fileId);
    setNotes(
      notes.map((note) =>
        note.id === noteId ? { ...note, files: note.files.filter((file) => file.id !== fileId) } : note,
      ),
    );
  }

  if (!user) {
    return (
      <main className="shell">
        <div className="brand">
          <span className="mark">K</span>
          <span className="brand-name">Knowledge</span>
        </div>
        <h1>A quiet place for what you know.</h1>
        <p className="lede">Keep notes, ideas, and references in one calm library.</p>
        <div className="actions">
          <Link className="button" to="/login">
            Log in
          </Link>
          <Link className="button ghost" to="/register">
            Create account
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="shell wide">
      <div className="topbar">
        <div className="brand">
          <span className="mark">K</span>
          <span className="brand-name">Knowledge</span>
        </div>
        <button type="button" className="ghost" onClick={onLogout}>
          Log out
        </button>
      </div>
      <p className="lede">
        Signed in as <strong>{user.nickname}</strong>
      </p>
      <section className="card">
        <h1>{editing ? "Edit note" : "New note"}</h1>
        <form className="auth-form" onSubmit={onSave}>
          <label>
            Title
            <input name="title" required defaultValue={editing?.title ?? ""} key={`title-${editing?.id ?? "new"}`} />
          </label>
          <label>
            Tags
            <input
              name="tags"
              placeholder="comma separated"
              defaultValue={editing?.tags.join(", ") ?? ""}
              key={`tags-${editing?.id ?? "new"}`}
            />
          </label>
          <label>
            Content
            <textarea
              name="content"
              rows={6}
              defaultValue={editing?.content ?? ""}
              key={`content-${editing?.id ?? "new"}`}
            />
          </label>
          <label>
            Files
            <input
              type="file"
              accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
              multiple
              disabled={busy}
              onChange={(event) => {
                const picked = Array.from(event.target.files ?? []).filter((file) => FILE_OK.test(file.name));
                setPending([...pending, ...picked]);
                event.target.value = "";
              }}
            />
          </label>
          {pending.length ? (
            <ul className="files">
              {pending.map((file, index) => (
                <li key={`${file.name}-${index}`}>
                  <span>{file.name}</span>
                  {busy ? (
                    <span className="spinner" aria-hidden />
                  ) : (
                    <button type="button" className="ghost" onClick={() => setPending(pending.filter((_, i) => i !== index))}>
                      Remove
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : null}
          {busy ? (
            <p className="upload-status" role="status">
              <span className="spinner" aria-hidden />
              {progress}
            </p>
          ) : null}
          {error ? <p className="error">{error}</p> : null}
          <div className="actions">
            <button type="submit" disabled={busy}>
              {editing ? "Save" : "Add note"}
            </button>
            {editing ? (
              <button
                type="button"
                className="ghost"
                onClick={() => {
                  setEditing(null);
                  setPending([]);
                }}
              >
                Cancel
              </button>
            ) : null}
          </div>
        </form>
      </section>
      <ul className="notes">
        {notes.map((note) => (
          <li key={note.id} className="note">
            <h2>{note.title}</h2>
            {note.tags.length ? (
              <p className="tags">{note.tags.map((tag) => `#${tag}`).join(" ")}</p>
            ) : null}
            {note.content ? <p>{note.content}</p> : null}
            {note.files.length ? (
              <ul className="files">
                {note.files.map((file) => (
                  <li key={file.id}>
                    <a href={noteFileUrl(note.id, file.id)} target="_blank" rel="noreferrer">
                      {file.name}
                    </a>
                    <button type="button" className="ghost" onClick={() => onRemoveFile(note.id, file.id)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            <div className="actions">
              <button type="button" className="ghost" onClick={() => setEditing(note)}>
                Edit
              </button>
              <button type="button" className="ghost" onClick={() => onDelete(note.id)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
