import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { FeedList } from "../components/FeedList";
import { LibraryCard } from "../components/LibraryCard";
import { NoteForm } from "../components/NoteForm";
import { Topbar } from "../components/Topbar";
import { errMsg, keepBusy, tagsFrom } from "../lib/files";
import {
  createNote,
  deleteFile,
  deleteNote,
  deleteNoteFile,
  getMe,
  listFeed,
  logout,
  updateNote,
  uploadFile,
  uploadNoteFile,
  type FeedItem,
  type Note,
  type User,
} from "../services/api";
import { Landing } from "./Landing";

function cursor(items: FeedItem[]) {
  const last = items[items.length - 1];
  if (!last) return undefined;
  return { before_id: last.id, before_kind: last.kind, before_created_at: last.created_at };
}

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [editing, setEditing] = useState<Note | null>(null);
  const [pending, setPending] = useState<File[]>([]);
  const [loose, setLoose] = useState<File[]>([]);
  const [busy, setBusy] = useState<"note" | "files" | "">("");
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");
  const [fileError, setFileError] = useState("");
  const [query, setQuery] = useState("");
  const [q, setQ] = useState("");
  const [ready, setReady] = useState(false);
  const feedRef = useRef(feed);
  const hasMoreRef = useRef(hasMore);
  const qRef = useRef(q);
  const loadingRef = useRef(false);
  const genRef = useRef(0);
  feedRef.current = feed;
  hasMoreRef.current = hasMore;
  qRef.current = q;

  const reloadFirstPage = useCallback(async () => {
    const gen = ++genRef.current;
    loadingRef.current = true;
    try {
      const page = await listFeed(undefined, undefined, qRef.current || undefined);
      if (gen !== genRef.current) return;
      setFeed(page.items);
      setHasMore(page.has_more);
      setReady(true);
    } catch {
      if (gen === genRef.current) {
        setFeed([]);
        setHasMore(false);
      }
    } finally {
      if (gen === genRef.current) loadingRef.current = false;
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loadingRef.current || !hasMoreRef.current) return;
    const gen = genRef.current;
    loadingRef.current = true;
    try {
      const page = await listFeed(cursor(feedRef.current), undefined, qRef.current || undefined);
      if (gen !== genRef.current) return;
      setFeed((prev) => {
        const seen = new Set(prev.map((item) => `${item.kind}:${item.id}`));
        return [...prev, ...page.items.filter((item) => !seen.has(`${item.kind}:${item.id}`))];
      });
      setHasMore(page.has_more);
    } catch {
      if (gen === genRef.current) setHasMore(false);
    } finally {
      if (gen === genRef.current) loadingRef.current = false;
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => setQ(query.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) return;
    void reloadFirstPage();
  }, [user, q, reloadFirstPage]);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
    setFeed([]);
    setHasMore(false);
    setReady(false);
    setQuery("");
    setQ("");
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
      if (qRef.current) await reloadFirstPage();
      else {
        const item: FeedItem = { kind: "note", ...note };
        setFeed(editing ? feed.map((row) => (row.kind === "note" && row.id === note.id ? item : row)) : [item, ...feed]);
      }
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
      const uploaded: FeedItem[] = [];
      let i = 0;
      for (const file of loose) {
        i += 1;
        uploaded.push({
          kind: "file",
          ...(await uploadFile(file, (pct) => {
            setProgress(`Uploading ${file.name} (${i}/${loose.length}) ${pct}%`);
          })),
        });
      }
      if (qRef.current) await reloadFirstPage();
      else setFeed([...uploaded, ...feed]);
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
    setFeed(feed.filter((item) => !(item.kind === "note" && item.id === id)));
    if (editing?.id === id) {
      setEditing(null);
      setPending([]);
    }
  }

  if (!user) return <Landing />;

  return (
    <main className="shell wide">
      <Topbar nickname={user.nickname} onLogout={onLogout} />
      <div className="compose">
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
          loose={loose}
          busy={busy === "files"}
          locked={!!busy}
          progress={progress}
          error={fileError}
          onSubmit={onSaveFiles}
          onPick={(files) => setLoose([...loose, ...files])}
          onRemoveLoose={(index) => setLoose(loose.filter((_, i) => i !== index))}
        />
      </div>
      <label className="search">
        Search
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Name, note content, or attached file"
        />
      </label>
      {ready ? (
      <FeedList
        items={feed}
        hasMore={hasMore}
        empty={q ? "Nothing matches." : "No notes or files yet."}
        q={q}
        onLoadMore={loadMore}
        onEdit={setEditing}
        onDeleteNote={onDeleteNote}
        onRemoveFile={async (noteId, fileId) => {
          await deleteNoteFile(noteId, fileId);
          setFeed(
            feed.map((item) =>
              item.kind === "note" && item.id === noteId
                ? { ...item, files: item.files.filter((file) => file.id !== fileId) }
                : item,
            ),
          );
        }}
        onDeleteFile={async (id) => {
          await deleteFile(id);
          setFeed(feed.filter((item) => !(item.kind === "file" && item.id === id)));
        }}
      />
      ) : null}
    </main>
  );
}
