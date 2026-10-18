import { useWindowVirtualizer } from "@tanstack/react-virtual";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { fileKind } from "../lib/files";
import { fileUrl, noteFileUrl, type FeedItem, type Note } from "../services/api";
import { Hit } from "./Hit";
import { StoredFiles } from "./StoredFiles";

export function FeedList({
  items,
  hasMore,
  empty,
  q,
  onLoadMore,
  onEdit,
  onDeleteNote,
  onRemoveFile,
  onDeleteFile,
}: {
  items: FeedItem[];
  hasMore: boolean;
  empty: string;
  q: string;
  onLoadMore: () => void;
  onEdit: (note: Note) => void;
  onDeleteNote: (id: number) => void;
  onRemoveFile: (noteId: number, fileId: number) => void;
  onDeleteFile: (id: number) => void;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  const [scrollMargin, setScrollMargin] = useState(0);
  const virtualizer = useWindowVirtualizer({
    count: items.length,
    estimateSize: (index) => (items[index]?.kind === "file" ? 160 : 200),
    overscan: 6,
    scrollMargin,
  });
  const lastIndex = virtualizer.getVirtualItems().at(-1)?.index;

  useLayoutEffect(() => {
    setScrollMargin(listRef.current?.offsetTop ?? 0);
  }, [items.length]);

  useEffect(() => {
    if (!hasMore || lastIndex == null) return;
    if (lastIndex >= items.length - 4) onLoadMore();
  }, [hasMore, items.length, lastIndex, onLoadMore]);

  if (!items.length) return <p className="muted tape-empty">{empty}</p>;

  return (
    <div ref={listRef} className="tape">
      <div className="tape-space" style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((row) => {
          const item = items[row.index];
          if (!item) return null;
          return (
            <div
              key={row.key}
              data-index={row.index}
              ref={virtualizer.measureElement}
              className="tape-item"
              style={{ transform: `translateY(${row.start - scrollMargin}px)` }}
            >
              {item.kind === "note" ? (
                <article className="note">
                  <h2>
                    <Hit text={item.title} q={q} />
                  </h2>
                  {item.tags.length ? <p className="tags">{item.tags.map((tag) => `#${tag}`).join(" ")}</p> : null}
                  {item.content ? (
                    <p>
                      <Hit text={item.content} q={q} />
                    </p>
                  ) : null}
                  <StoredFiles
                    files={item.files}
                    q={q}
                    href={(id) => noteFileUrl(item.id, id)}
                    action="Remove"
                    onAction={(id) => onRemoveFile(item.id, id)}
                  />
                  <div className="actions">
                    <button type="button" className="ghost" onClick={() => onEdit(item)}>
                      Edit
                    </button>
                    <button type="button" className="ghost" onClick={() => onDeleteNote(item.id)}>
                      Delete
                    </button>
                  </div>
                </article>
              ) : (
                <article className="file-card">
                  <p className="file-type">{fileKind(item.name)}</p>
                  <h2>
                    <Hit text={item.name} q={q} />
                  </h2>
                  <div className="actions">
                    <a className="button ghost" href={fileUrl(item.id)} target="_blank" rel="noreferrer">
                      Open
                    </a>
                    <button type="button" className="ghost" onClick={() => onDeleteFile(item.id)}>
                      Delete
                    </button>
                  </div>
                </article>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
