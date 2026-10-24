import { FormEvent, useState } from "react";
import { errMsg, keepBusy, tagsFrom } from "../lib/files";
import {
  createNote,
  deleteNote,
  deleteNoteFile,
  updateNote,
  uploadNoteFile,
  type FeedItem,
  type Note,
} from "../services/api";

export function useNotes(feed: {
  items: FeedItem[];
  setItems: (value: FeedItem[] | ((prev: FeedItem[]) => FeedItem[])) => void;
  qRef: { current: string };
  reloadFirstPage: () => Promise<void>;
}) {
  const [editing, setEditing] = useState<Note | null>(null);
  const [pending, setPending] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");

  function cancel() {
    setEditing(null);
    setPending([]);
  }

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError("");
    setBusy(true);
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
      if (feed.qRef.current) await feed.reloadFirstPage();
      else {
        const item: FeedItem = { kind: "note", ...note };
        feed.setItems(editing ? feed.items.map((row) => (row.kind === "note" && row.id === note.id ? item : row)) : [item, ...feed.items]);
      }
      cancel();
      form.reset();
      return true;
    } catch (err) {
      setError(errMsg(err, "Could not save note"));
      return false;
    } finally {
      await keepBusy(started);
      setBusy(false);
      setProgress("");
    }
  }

  async function onDelete(id: number) {
    await deleteNote(id);
    feed.setItems(feed.items.filter((item) => !(item.kind === "note" && item.id === id)));
    if (editing?.id === id) cancel();
  }

  async function onRemoveFile(noteId: number, fileId: number) {
    await deleteNoteFile(noteId, fileId);
    feed.setItems(
      feed.items.map((item) =>
        item.kind === "note" && item.id === noteId ? { ...item, files: item.files.filter((file) => file.id !== fileId) } : item,
      ),
    );
  }

  return {
    editing,
    pending,
    busy,
    progress,
    error,
    setEditing,
    setPending,
    cancel,
    onSave,
    onDelete,
    onRemoveFile,
  };
}
