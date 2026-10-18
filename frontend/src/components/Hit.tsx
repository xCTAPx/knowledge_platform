function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function Hit({ text, q }: { text: string; q: string }) {
  if (!q) return text;
  return text.split(new RegExp(`(${escapeRegExp(q)})`, "gi")).map((part, index) =>
    part.toLowerCase() === q.toLowerCase() ? (
      <mark className="hit" key={index}>
        {part}
      </mark>
    ) : (
      part
    ),
  );
}
