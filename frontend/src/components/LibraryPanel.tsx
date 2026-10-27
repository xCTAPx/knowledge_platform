import { useEffect, useState } from "react";
import { type FeedItem, type Note } from "../services/api";
import { FeedList } from "./FeedList";
import { SearchBox } from "./SearchBox";
import "./LibraryPanel.css";

export function LibraryPanel({
  query,
  q,
  items,
  hasMore,
  ready,
  onQuery,
  onLoadMore,
  onEdit,
  onDeleteNote,
  onRemoveFile,
  onDeleteFile,
}: {
  query: string;
  q: string;
  items: FeedItem[];
  hasMore: boolean;
  ready: boolean;
  onQuery: (value: string) => void;
  onLoadMore: () => void;
  onEdit: (note: Note) => void;
  onDeleteNote: (id: number) => void;
  onRemoveFile: (noteId: number, fileId: number) => void;
  onDeleteFile: (id: number) => void;
}) {
  const [notes, setNotes] = useState(true);
  const [files, setFiles] = useState(true);
  const visible = items.filter((item) => (item.kind === "note" ? notes : files));
  const empty =
    !notes && !files
      ? "Notes and files are hidden."
      : q
        ? "Nothing matches."
        : !notes
          ? "No files yet."
          : !files
            ? "No notes yet."
            : "No notes or files yet.";

  useEffect(() => {
    if (!ready || !hasMore || (!notes && !files)) return;
    if (visible.length < 6) onLoadMore();
  }, [ready, hasMore, notes, files, visible.length, onLoadMore]);

  return (
    <section className="library">
      <header className="library-head">
        <h2>Library</h2>
        <div className="library-filters">
          <button type="button" className="ghost" aria-pressed={notes} onClick={() => setNotes((on) => !on)}>
            Notes
          </button>
          <button type="button" className="ghost" aria-pressed={files} onClick={() => setFiles((on) => !on)}>
            Files
          </button>
        </div>
      </header>
      <SearchBox value={query} onChange={onQuery} />
      {ready ? (
        <FeedList
          items={visible}
          hasMore={hasMore}
          empty={empty}
          q={q}
          onLoadMore={onLoadMore}
          onEdit={onEdit}
          onDeleteNote={onDeleteNote}
          onRemoveFile={onRemoveFile}
          onDeleteFile={onDeleteFile}
        />
      ) : null}
    </section>
  );
}
