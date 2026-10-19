import { FormEvent } from "react";
import { isolateSubmit } from "../lib/forms";
import { FilePicker } from "./FilePicker";
import { PendingFiles } from "./PendingFiles";
import { UploadStatus } from "./UploadStatus";

export function LibraryCard({
  loose,
  busy,
  locked,
  progress,
  error,
  onSubmit,
  onPick,
  onRemoveLoose,
}: {
  loose: File[];
  busy: boolean;
  locked: boolean;
  progress: string;
  error: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onPick: (files: File[]) => void;
  onRemoveLoose: (index: number) => void;
}) {
  return (
    <section className="card">
      <h1>Add files</h1>
      <p className="lede">PDF, txt, or Markdown without a note.</p>
      <form className="auth-form" onSubmit={isolateSubmit(onSubmit)}>
        <FilePicker disabled={busy} onPick={onPick} />
        <PendingFiles files={loose} busy={busy} onRemove={onRemoveLoose} />
        {busy ? <UploadStatus text={progress} /> : null}
        {error ? <p className="error">{error}</p> : null}
        <div className="actions">
          <button type="submit" disabled={locked || !loose.length}>
            Save files
          </button>
        </div>
      </form>
    </section>
  );
}
