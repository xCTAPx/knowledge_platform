import "./StoredFiles.css";
import "./UploadStatus.css";

export function PendingFiles({
  files,
  busy,
  onRemove,
}: {
  files: File[];
  busy: boolean;
  onRemove: (index: number) => void;
}) {
  if (!files.length) return null;
  return (
    <ul className="files">
      {files.map((file, index) => (
        <li key={`${file.name}-${index}`}>
          <span>{file.name}</span>
          {busy ? (
            <span className="spinner" aria-hidden />
          ) : (
            <button type="button" className="ghost" onClick={() => onRemove(index)}>
              Remove
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
