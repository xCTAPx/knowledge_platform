import { useState } from "react";
import { ChatPanel } from "../components/ChatPanel";
import { ComposeDrawer } from "../components/ComposeDrawer";
import { LibraryCard } from "../components/LibraryCard";
import { LibraryPanel } from "../components/LibraryPanel";
import { NoteForm } from "../components/NoteForm";
import { Topbar } from "../components/Topbar";
import { useChats } from "../hooks/useChats";
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
  const chats = useChats(auth.user);
  const locked = notes.busy || files.busy || chats.busy;
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
      <ChatPanel
        chats={chats.chats}
        messages={chats.messages}
        activeId={chats.activeId}
        value={chats.value}
        busy={chats.busy}
        locked={locked}
        error={chats.error}
        canNew={chats.canNew}
        onSelect={chats.setActiveId}
        onNew={chats.newChat}
        onRename={chats.renameChat}
        onRemove={chats.removeChat}
        onChange={chats.setValue}
        onSubmit={chats.onSubmit}
      />
      <LibraryPanel
        query={feed.query}
        q={feed.q}
        items={feed.items}
        hasMore={feed.hasMore}
        ready={feed.ready}
        onQuery={feed.setQuery}
        onLoadMore={feed.loadMore}
        onEdit={openEdit}
        onDeleteNote={notes.onDelete}
        onRemoveFile={notes.onRemoveFile}
        onDeleteFile={files.onDelete}
      />
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
