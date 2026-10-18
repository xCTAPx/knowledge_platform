import { FormEvent } from "react";
import { type Note } from "../services/api";
import { FilePicker } from "./FilePicker";
import { PendingFiles } from "./PendingFiles";
import { UploadStatus } from "./UploadStatus";

export function NoteForm({
  editing,
  pending,
  busy,
  locked,
  progress,
  error,
  onSubmit,
  onPick,
  onRemovePending,
  onCancel,
}: {
  editing: Note | null;
  pending: File[];
  busy: boolean;
  locked: boolean;
  progress: string;
  error: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onPick: (files: File[]) => void;
  onRemovePending: (index: number) => void;
  onCancel: () => void;
}) {
  const key = editing?.id ?? "new";
  return (
    <section className="card">
      <h1>{editing ? "Edit note" : "New note"}</h1>
      <form className="auth-form" onSubmit={onSubmit}>
        <label>
          Title
          <input name="title" required defaultValue={editing?.title ?? ""} key={`title-${key}`} />
        </label>
        <label>
          Tags
          <input
            name="tags"
            placeholder="comma separated"
            defaultValue={editing?.tags.join(", ") ?? ""}
            key={`tags-${key}`}
          />
        </label>
        <label>
          Content
          <textarea name="content" rows={4} defaultValue={editing?.content ?? ""} key={`content-${key}`} />
        </label>
        <FilePicker disabled={busy} onPick={onPick} />
        <PendingFiles files={pending} busy={busy} onRemove={onRemovePending} />
        {busy ? <UploadStatus text={progress} /> : null}
        {error ? <p className="error">{error}</p> : null}
        <div className="actions">
          <button type="submit" disabled={locked}>
            {editing ? "Save" : "Add note"}
          </button>
          {editing ? (
            <button type="button" className="ghost" onClick={onCancel}>
              Cancel
            </button>
          ) : null}
        </div>
      </form>
    </section>
  );
}
