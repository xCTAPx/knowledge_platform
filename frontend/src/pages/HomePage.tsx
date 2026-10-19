import { AskBox } from "../components/AskBox";
import { Compose } from "../components/Compose";
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
import { Landing } from "./Landing";

export default function HomePage() {
  const auth = useAuth();
  const feed = useFeed(auth.user);
  const notes = useNotes(feed);
  const files = useFiles(feed);
  const ask = useAsk();
  const locked = notes.busy || files.busy || ask.busy;

  if (!auth.user) return <Landing />;

  return (
    <main className="shell wide">
      <Topbar nickname={auth.user.nickname} onLogout={auth.onLogout} />
      <Compose>
        <NoteForm
          editing={notes.editing}
          pending={notes.pending}
          busy={notes.busy}
          locked={locked}
          progress={notes.progress}
          error={notes.error}
          onSubmit={notes.onSave}
          onPick={(picked) => notes.setPending([...notes.pending, ...picked])}
          onRemovePending={(index) => notes.setPending(notes.pending.filter((_, i) => i !== index))}
          onCancel={notes.cancel}
        />
        <LibraryCard
          loose={files.loose}
          busy={files.busy}
          locked={locked}
          progress={files.progress}
          error={files.error}
          onSubmit={files.onSave}
          onPick={(picked) => files.setLoose([...files.loose, ...picked])}
          onRemoveLoose={(index) => files.setLoose(files.loose.filter((_, i) => i !== index))}
        />
      </Compose>
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
          onEdit={notes.setEditing}
          onDeleteNote={notes.onDelete}
          onRemoveFile={notes.onRemoveFile}
          onDeleteFile={files.onDelete}
        />
      ) : null}
    </main>
  );
}
