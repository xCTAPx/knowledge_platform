import { useCallback, useEffect, useRef, useState } from "react";
import { feedCursor } from "../lib/feed";
import { listFeed, type FeedItem, type User } from "../services/api";

export function useFeed(user: User | null) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [query, setQuery] = useState("");
  const [q, setQ] = useState("");
  const [ready, setReady] = useState(false);
  const itemsRef = useRef(items);
  const hasMoreRef = useRef(hasMore);
  const qRef = useRef(q);
  const loadingRef = useRef(false);
  const genRef = useRef(0);
  itemsRef.current = items;
  hasMoreRef.current = hasMore;
  qRef.current = q;

  const reloadFirstPage = useCallback(async () => {
    const gen = ++genRef.current;
    loadingRef.current = true;
    try {
      const page = await listFeed(undefined, undefined, qRef.current || undefined);
      if (gen !== genRef.current) return;
      setItems(page.items);
      setHasMore(page.has_more);
      setReady(true);
    } catch {
      if (gen === genRef.current) {
        setItems([]);
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
      const page = await listFeed(feedCursor(itemsRef.current), undefined, qRef.current || undefined);
      if (gen !== genRef.current) return;
      setItems((prev) => {
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
    if (!user) {
      setItems([]);
      setHasMore(false);
      setReady(false);
      setQuery("");
      setQ("");
      return;
    }
    void reloadFirstPage();
  }, [user, q, reloadFirstPage]);

  return { items, setItems, hasMore, query, setQuery, q, qRef, ready, loadMore, reloadFirstPage };
}
