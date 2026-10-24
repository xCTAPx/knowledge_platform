import { ReactNode, useEffect } from "react";
import "./Drawer.css";

export function Drawer({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="drawer-back" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()} role="dialog" aria-label={title}>
        <header className="drawer-head">
          <h1>{title}</h1>
          <button type="button" className="ghost" onClick={onClose}>
            Close
          </button>
        </header>
        {children}
      </aside>
    </div>
  );
}
