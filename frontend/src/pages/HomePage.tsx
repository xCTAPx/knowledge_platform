import { useState } from "react";
import { AskBox } from "../components/AskBox";
import { ComposeDrawer } from "../components/ComposeDrawer";
import { FeedList } from "../components/FeedList";
import { LibraryCard } from "../components/LibraryCard";
import { NoteForm } from "../components/NoteForm";
import { SearchBox } from "../components/SearchBox";
import { Topbar } from "../components/Topbar";
import { useAsk } from "../hooks/useAsk";
import { useAuth } from "../hooks/useAuth";
import { useFeed } from "../hooks/useFeed";
import { useFiles } from "../hooks/useFiles";
import { useNotes } from "../hooks/useNotes";
import { type Note } from "../services/api";
import { Landing } from "./Landing";

export default function HomePage() {
  const auth = useAuth();
  const feed = useFeed(auth.user);
  const notes = useNotes(feed);
  const files = useFiles(feed);
  const ask = useAsk();
  const locked = notes.busy || files.busy || ask.busy;
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"note" | "file">("note");

  function closeCompose() {
    notes.cancel();
    files.setLoose([]);
    setOpen(false);
  }

  function openAdd() {
    notes.cancel();
    files.setLoose([]);
    setKind("note");
    setOpen(true);
  }

  function openEdit(note: Note) {
    notes.setEditing(note);
    setKind("note");
    setOpen(true);
  }

  if (!auth.user) return <Landing />;

  return (
    <main className="shell wide">
      <Topbar nickname={auth.user.nickname} onAdd={openAdd} onLogout={auth.onLogout} />
      <SearchBox value={feed.query} onChange={feed.setQuery} />
      <AskBox
        value={ask.value}
        busy={ask.busy}
        locked={locked}
        error={ask.error}
        answer={ask.answer}
        onChange={ask.setValue}
        onSubmit={ask.onSubmit}
      />
      {feed.ready ? (
        <FeedList
          items={feed.items}
          hasMore={feed.hasMore}
          empty={feed.q ? "Nothing matches." : "No notes or files yet."}
          q={feed.q}
          onLoadMore={feed.loadMore}
          onEdit={openEdit}
          onDeleteNote={notes.onDelete}
          onRemoveFile={notes.onRemoveFile}
          onDeleteFile={files.onDelete}
        />
      ) : null}
      <ComposeDrawer
        open={open}
        kind={kind}
        editing={Boolean(notes.editing)}
        onKind={setKind}
        onClose={closeCompose}
        note={
          <NoteForm
            editing={notes.editing}
            pending={notes.pending}
            busy={notes.busy}
            locked={locked}
            progress={notes.progress}
            error={notes.error}
            onSubmit={async (event) => {
              if (await notes.onSave(event)) setOpen(false);
            }}
            onPick={(picked) => notes.setPending([...notes.pending, ...picked])}
            onRemovePending={(index) => notes.setPending(notes.pending.filter((_, i) => i !== index))}
          />
        }
        file={
          <LibraryCard
            loose={files.loose}
            busy={files.busy}
            locked={locked}
            progress={files.progress}
            error={files.error}
            onSubmit={async (event) => {
              if (await files.onSave(event)) setOpen(false);
            }}
            onPick={(picked) => files.setLoose([...files.loose, ...picked])}
            onRemoveLoose={(index) => files.setLoose(files.loose.filter((_, i) => i !== index))}
          />
        }
      />
    </main>
  );
}
