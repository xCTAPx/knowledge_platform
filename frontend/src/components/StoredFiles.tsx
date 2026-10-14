export function StoredFiles({
  files,
  href,
  action,
  onAction,
}: {
  files: { id: number; name: string }[];
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
            {file.name}
          </a>
          <button type="button" className="ghost" onClick={() => onAction(file.id)}>
            {action}
          </button>
        </li>
      ))}
    </ul>
  );
}
