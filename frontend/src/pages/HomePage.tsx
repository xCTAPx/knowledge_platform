import { FormEvent, useEffect, useState } from "react";
import { LibraryCard } from "../components/LibraryCard";
import { NoteForm } from "../components/NoteForm";
import { NoteList } from "../components/NoteList";
import { Topbar } from "../components/Topbar";
import { errMsg, keepBusy, tagsFrom } from "../lib/files";
import {
  createNote,
  deleteFile,
  deleteNote,
  deleteNoteFile,
  getMe,
  listFiles,
  listNotes,
  logout,
  updateNote,
  uploadFile,
  uploadNoteFile,
  type Note,
  type NoteFile,
  type User,
} from "../services/api";
import { Landing } from "./Landing";

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [library, setLibrary] = useState<NoteFile[]>([]);
  const [editing, setEditing] = useState<Note | null>(null);
  const [pending, setPending] = useState<File[]>([]);
  const [loose, setLoose] = useState<File[]>([]);
  const [busy, setBusy] = useState<"note" | "files" | "">("");
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");
  const [fileError, setFileError] = useState("");

  useEffect(() => {
    getMe()
      .then(async (me) => {
        setUser(me);
        const [noteRows, fileRows] = await Promise.all([listNotes(), listFiles()]);
        setNotes(noteRows);
        setLibrary(fileRows);
      })
      .catch(() => setUser(null));
  }, []);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
    setNotes([]);
    setLibrary([]);
  }

  async function onSaveNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError("");
    setBusy("note");
    setProgress(pending.length ? "Uploading files…" : "Saving…");
    const started = Date.now();
    try {
      let note = editing
        ? await updateNote(editing.id, String(data.get("title")), tagsFrom(String(data.get("tags") ?? "")), String(data.get("content") ?? ""))
        : await createNote(String(data.get("title")), tagsFrom(String(data.get("tags") ?? "")), String(data.get("content") ?? ""));
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
      setError(errMsg(err, "Could not save note"));
    } finally {
      await keepBusy(started);
      setBusy("");
      setProgress("");
    }
  }

  async function onSaveFiles(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loose.length) return;
    const form = event.currentTarget;
    setFileError("");
    setBusy("files");
    setProgress("Uploading files…");
    const started = Date.now();
    try {
      const uploaded: NoteFile[] = [];
      let i = 0;
      for (const file of loose) {
        i += 1;
        uploaded.push(
          await uploadFile(file, (pct) => {
            setProgress(`Uploading ${file.name} (${i}/${loose.length}) ${pct}%`);
          }),
        );
      }
      setLibrary([...uploaded, ...library]);
      setLoose([]);
      form.reset();
    } catch (err) {
      setFileError(errMsg(err, "Could not save file"));
    } finally {
      await keepBusy(started);
      setBusy("");
      setProgress("");
    }
  }

  async function onDeleteNote(id: number) {
    await deleteNote(id);
    setNotes(notes.filter((note) => note.id !== id));
    if (editing?.id === id) {
      setEditing(null);
      setPending([]);
    }
  }

  if (!user) return <Landing />;

  return (
    <main className="shell wide">
      <Topbar nickname={user.nickname} onLogout={onLogout} />
      <NoteForm
        editing={editing}
        pending={pending}
        busy={busy === "note"}
        locked={!!busy}
        progress={progress}
        error={error}
        onSubmit={onSaveNote}
        onPick={(files) => setPending([...pending, ...files])}
        onRemovePending={(index) => setPending(pending.filter((_, i) => i !== index))}
        onCancel={() => {
          setEditing(null);
          setPending([]);
        }}
      />
      <LibraryCard
        library={library}
        loose={loose}
        busy={busy === "files"}
        locked={!!busy}
        progress={progress}
        error={fileError}
        onSubmit={onSaveFiles}
        onPick={(files) => setLoose([...loose, ...files])}
        onRemoveLoose={(index) => setLoose(loose.filter((_, i) => i !== index))}
        onDelete={async (id) => {
          await deleteFile(id);
          setLibrary(library.filter((item) => item.id !== id));
        }}
      />
      <NoteList
        notes={notes}
        onEdit={setEditing}
        onDelete={onDeleteNote}
        onRemoveFile={async (noteId, fileId) => {
          await deleteNoteFile(noteId, fileId);
          setNotes(
            notes.map((note) =>
              note.id === noteId ? { ...note, files: note.files.filter((file) => file.id !== fileId) } : note,
            ),
          );
        }}
      />
    </main>
  );
}
