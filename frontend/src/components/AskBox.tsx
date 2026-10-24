import { FormEvent } from "react";
import { isolateSubmit } from "../lib/forms";
import "./AskBox.css";

export function AskBox({
  value,
  busy,
  locked,
  error,
  answer,
  onChange,
  onSubmit,
}: {
  value: string;
  busy: boolean;
  locked: boolean;
  error: string;
  answer: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="ask" onSubmit={isolateSubmit(onSubmit)}>
      <label>
        Ask
        <textarea
          rows={4}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key !== "Enter" || event.shiftKey) return;
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
          }}
          placeholder="Question about your notes and files"
          disabled={busy}
        />
      </label>
      <button type="submit" disabled={locked || !value.trim()}>
        {busy ? "Asking…" : "Ask"}
      </button>
      {error ? <p className="error">{error}</p> : null}
      {answer || busy ? <p className={busy ? "answer streaming" : "answer"}>{answer}</p> : null}
    </form>
  );
}
