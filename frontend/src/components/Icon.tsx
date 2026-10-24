import "./Icon.css";

const paths = {
  plus: "M12 5v14M5 12h14",
  pencil: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2",
  eye: ["M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z", "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"],
  close: "M18 6 6 18M6 6l12 12",
};

export function Icon({ name }: { name: keyof typeof paths }) {
  const d = paths[name];
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      {(Array.isArray(d) ? d : [d]).map((path) => (
        <path key={path} d={path} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      ))}
    </svg>
  );
}
