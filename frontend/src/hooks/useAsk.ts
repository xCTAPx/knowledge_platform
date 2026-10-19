import { FormEvent, useState } from "react";
import { errMsg } from "../lib/files";
import { askLibrary } from "../services/api";

export function useAsk() {
  const [value, setValue] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = value.trim();
    if (!q) return;
    setError("");
    setAnswer("");
    setBusy(true);
    try {
      setAnswer((await askLibrary(q)).answer);
    } catch (err) {
      setError(errMsg(err, "Could not ask"));
    } finally {
      setBusy(false);
    }
  }

  return { value, setValue, answer, error, busy, onSubmit };
}
