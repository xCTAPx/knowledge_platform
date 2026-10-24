import { useWindowVirtualizer } from "@tanstack/react-virtual";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { fileKind } from "../lib/files";
import { fileUrl, noteFileUrl, type FeedItem, type Note } from "../services/api";
import { FilePreview } from "./FilePreview";
import { Hit } from "./Hit";
import { Icon } from "./Icon";
import { StoredFiles } from "./StoredFiles";
import "./FeedList.css";

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
  const [preview, setPreview] = useState<{ name: string; url: string } | null>(null);
  const virtualizer = useWindowVirtualizer({
    count: items.length,
    estimateSize: (index) => (items[index]?.kind === "file" ? 72 : 96),
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
                  <div className="tape-row">
                    <h2>
                      <Hit text={item.title} q={q} />
                    </h2>
                    <div className="actions">
                      <button type="button" className="ghost icon-btn" aria-label="Edit" onClick={() => onEdit(item)}>
                        <Icon name="pencil" />
                      </button>
                      <button type="button" className="ghost icon-btn" aria-label="Delete" onClick={() => onDeleteNote(item.id)}>
                        <Icon name="trash" />
                      </button>
                    </div>
                  </div>
                  {item.tags.length ? <p className="tags">{item.tags.map((tag) => `#${tag}`).join(" ")}</p> : null}
                  {item.content ? (
                    <p className="excerpt">
                      <Hit text={item.content} q={q} />
                    </p>
                  ) : null}
                  <StoredFiles
                    files={item.files}
                    q={q}
                    onPreview={(file) => setPreview({ name: file.name, url: noteFileUrl(item.id, file.id) })}
                    onAction={(id) => onRemoveFile(item.id, id)}
                  />
                </article>
              ) : (
                <article className="file-card">
                  <div className="tape-row">
                    <div>
                      <p className="file-type">{fileKind(item.name)}</p>
                      <h2>
                        <Hit text={item.name} q={q} />
                      </h2>
                    </div>
                    <div className="actions">
                      <button type="button" className="ghost icon-btn" aria-label="View" onClick={() => setPreview({ name: item.name, url: fileUrl(item.id) })}>
                        <Icon name="eye" />
                      </button>
                      <button type="button" className="ghost icon-btn" aria-label="Delete" onClick={() => onDeleteFile(item.id)}>
                        <Icon name="trash" />
                      </button>
                    </div>
                  </div>
                </article>
              )}
            </div>
          );
        })}
      </div>
      {preview ? <FilePreview name={preview.name} url={preview.url} onClose={() => setPreview(null)} /> : null}
    </div>
  );
}
