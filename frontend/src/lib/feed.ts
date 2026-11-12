import type { FeedItem, IndexState, IndexStatusName } from "../services/api";

export function feedCursor(items: FeedItem[]) {
  const last = items[items.length - 1];
  if (!last) return undefined;
  return { before_id: last.id, before_kind: last.kind, before_created_at: last.created_at };
}

export function indexing(item: FeedItem) {
  if (item.index_status === "pending") return true;
  return item.kind === "note" && item.files.some((file) => file.index_status === "pending");
}

export function applyIndexStatus(items: FeedItem[], rows: IndexState[]) {
  const notes = new Map<number, IndexState["index_status"]>();
  const files = new Map<number, IndexState["index_status"]>();
  for (const row of rows) (row.kind === "note" ? notes : files).set(row.id, row.index_status);
  return items.map((item) => {
    if (item.kind === "file") {
      const index_status: IndexStatusName = files.get(item.id) ?? "ready";
      return index_status === item.index_status ? item : { ...item, index_status };
    }

    const index_status: IndexStatusName = notes.get(item.id) ?? "ready";
    let changed = index_status !== item.index_status;
    const nextFiles = item.files.map((file) => {
      const fileStatus: IndexStatusName = files.get(file.id) ?? "ready";
      if (fileStatus === file.index_status) return file;
      changed = true;
      return { ...file, index_status: fileStatus };
    });
    return changed ? { ...item, index_status, files: nextFiles } : item;
  });
}
