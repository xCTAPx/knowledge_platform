import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { isMd, isPdf } from "../lib/files";
import { Modal } from "./Modal";
import "./FilePreview.css";

export function FilePreview({ name, url, onClose }: { name: string; url: string; onClose: () => void }) {
  const pdf = isPdf(name);
  const md = isMd(name);
  const [text, setText] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (pdf) return;
    const ac = new AbortController();
    fetch(url, { credentials: "include", signal: ac.signal })
      .then((res) => {
        if (!res.ok) throw new Error("Could not open file");
        return res.text();
      })
      .then(setText)
      .catch((err) => {
        if (!ac.signal.aborted) setError(err instanceof Error ? err.message : "Could not open file");
      });
    return () => ac.abort();
  }, [pdf, url]);

  return (
    <Modal title={name} onClose={onClose}>
      {pdf ? (
        <iframe className="preview-frame" src={url} title={name} />
      ) : error ? (
        <p className="error">{error}</p>
      ) : md ? (
        <div className="preview-md">{text ? <Markdown>{text}</Markdown> : "Loading…"}</div>
      ) : (
        <pre className="preview-text">{text || "Loading…"}</pre>
      )}
    </Modal>
  );
}
