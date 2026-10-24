import { FormEvent, useState } from "react";
import { errMsg, keepBusy } from "../lib/files";
import { deleteFile, uploadFile, type FeedItem } from "../services/api";

export function useFiles(feed: {
  items: FeedItem[];
  setItems: (value: FeedItem[] | ((prev: FeedItem[]) => FeedItem[])) => void;
  qRef: { current: string };
  reloadFirstPage: () => Promise<void>;
}) {
  const [loose, setLoose] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loose.length) return false;
    const form = event.currentTarget;
    setError("");
    setBusy(true);
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
      if (feed.qRef.current) await feed.reloadFirstPage();
      else feed.setItems([...uploaded, ...feed.items]);
      setLoose([]);
      form.reset();
      return true;
    } catch (err) {
      setError(errMsg(err, "Could not save file"));
      return false;
    } finally {
      await keepBusy(started);
      setBusy(false);
      setProgress("");
    }
  }

  async function onDelete(id: number) {
    await deleteFile(id);
    feed.setItems(feed.items.filter((item) => !(item.kind === "file" && item.id === id)));
  }

  return { loose, setLoose, busy, progress, error, onSave, onDelete };
}
