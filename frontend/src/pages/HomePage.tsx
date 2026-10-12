import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createNote,
  deleteNote,
  getMe,
  listNotes,
  logout,
  updateNote,
  type Note,
  type User,
} from "../services/api";

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
    try {
      if (editing) {
        const note = await updateNote(editing.id, title, tags, content);
        setNotes(notes.map((item) => (item.id === note.id ? note : item)));
        setEditing(null);
      } else {
        const note = await createNote(title, tags, content);
        setNotes([note, ...notes]);
      }
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save note");
    }
  }

  async function onDelete(id: number) {
    await deleteNote(id);
    setNotes(notes.filter((note) => note.id !== id));
    if (editing?.id === id) setEditing(null);
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
          {error ? <p className="error">{error}</p> : null}
          <div className="actions">
            <button type="submit">{editing ? "Save" : "Add note"}</button>
            {editing ? (
              <button type="button" className="ghost" onClick={() => setEditing(null)}>
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
