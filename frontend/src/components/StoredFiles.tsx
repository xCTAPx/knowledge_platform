import { Hit } from "./Hit";
import { Icon } from "./Icon";
import "./StoredFiles.css";

export function StoredFiles({
  files,
  q = "",
  onPreview,
  onAction,
}: {
  files: { id: number; name: string }[];
  q?: string;
  onPreview: (file: { id: number; name: string }) => void;
  onAction: (id: number) => void;
}) {
  if (!files.length) return null;
  return (
    <ul className="files">
      {files.map((file) => (
        <li key={file.id}>
          <button type="button" className="file-name" onClick={() => onPreview(file)}>
            <Hit text={file.name} q={q} />
          </button>
          <div className="actions">
            <button type="button" className="ghost icon-btn" aria-label="View" onClick={() => onPreview(file)}>
              <Icon name="eye" />
            </button>
            <button type="button" className="ghost icon-btn" aria-label="Delete" onClick={() => onAction(file.id)}>
              <Icon name="trash" />
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
