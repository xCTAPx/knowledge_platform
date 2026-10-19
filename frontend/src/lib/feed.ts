import type { FeedItem } from "../services/api";

export function feedCursor(items: FeedItem[]) {
  const last = items[items.length - 1];
  if (!last) return undefined;
  return { before_id: last.id, before_kind: last.kind, before_created_at: last.created_at };
}
