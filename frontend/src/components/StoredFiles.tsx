import { Hit } from "./Hit";

export function StoredFiles({
  files,
  q = "",
  href,
  action,
  onAction,
}: {
  files: { id: number; name: string }[];
  q?: string;
  href: (id: number) => string;
  action: string;
  onAction: (id: number) => void;
}) {
  if (!files.length) return null;
  return (
    <ul className="files">
      {files.map((file) => (
        <li key={file.id}>
          <a href={href(file.id)} target="_blank" rel="noreferrer">
            <Hit text={file.name} q={q} />
          </a>
          <button type="button" className="ghost" onClick={() => onAction(file.id)}>
            {action}
          </button>
        </li>
      ))}
    </ul>
  );
}
