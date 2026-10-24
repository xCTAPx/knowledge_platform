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
    <form className="auth-form" onSubmit={isolateSubmit(onSubmit)}>
      <p className="lede">PDF, txt, or Markdown.</p>
      <FilePicker disabled={busy} onPick={onPick} />
      <PendingFiles files={loose} busy={busy} onRemove={onRemoveLoose} />
      {busy ? <UploadStatus text={progress} /> : null}
      {error ? <p className="error">{error}</p> : null}
      <button type="submit" disabled={locked || !loose.length}>
        Save
      </button>
    </form>
  );
}
