import { ReactNode } from "react";
import { Drawer } from "./Drawer";
import "./ComposeDrawer.css";

export function ComposeDrawer({
  open,
  kind,
  editing,
  onKind,
  onClose,
  note,
  file,
}: {
  open: boolean;
  kind: "note" | "file";
  editing: boolean;
  onKind: (kind: "note" | "file") => void;
  onClose: () => void;
  note: ReactNode;
  file: ReactNode;
}) {
  if (!open) return null;
  return (
    <Drawer title={editing ? "Edit note" : "Add"} onClose={onClose}>
      {editing ? null : (
        <div className="kind-toggle">
          <button type="button" className={kind === "note" ? "on" : "ghost"} onClick={() => onKind("note")}>
            Note
          </button>
          <button type="button" className={kind === "file" ? "on" : "ghost"} onClick={() => onKind("file")}>
            File
          </button>
        </div>
      )}
      {kind === "note" ? note : file}
    </Drawer>
  );
}
