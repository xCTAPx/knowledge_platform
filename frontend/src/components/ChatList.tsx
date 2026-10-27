import { useState } from "react";
import { type Chat } from "../lib/chats";
import { Icon } from "./Icon";
import "./ChatList.css";

export function ChatList({
  chats,
  activeId,
  canNew,
  onSelect,
  onNew,
  onRename,
  onRemove,
}: {
  chats: Chat[];
  activeId: number | null;
  canNew: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
  onRename: (id: number, title: string) => void;
  onRemove: (id: number) => void;
}) {
  const [editId, setEditId] = useState<number | null>(null);
  const [title, setTitle] = useState("");

  function save() {
    if (editId == null) return;
    onRename(editId, title);
    setEditId(null);
  }

  return (
    <aside className="chat-list">
      <button type="button" disabled={!canNew} onClick={onNew}>
        <Icon name="plus" />
        New chat
      </button>
      <ul>
        {chats.map((chat) => (
          <li key={chat.id} className={chat.id === activeId ? "on" : undefined}>
            {editId === chat.id ? (
              <input
                className="chat-title"
                value={title}
                autoFocus
                onChange={(event) => setTitle(event.target.value)}
                onBlur={save}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    save();
                  }
                  if (event.key === "Escape") setEditId(null);
                }}
              />
            ) : (
              <button type="button" className="chat-title" onClick={() => onSelect(chat.id)}>
                {chat.title}
              </button>
            )}
            <button
              type="button"
              className="ghost icon-btn"
              aria-label="Rename"
              onClick={(event) => {
                event.stopPropagation();
                setEditId(chat.id);
                setTitle(chat.title);
              }}
            >
              <Icon name="pencil" />
            </button>
            <button
              type="button"
              className="ghost icon-btn"
              aria-label="Delete"
              onClick={(event) => {
                event.stopPropagation();
                onRemove(chat.id);
              }}
            >
              <Icon name="trash" />
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
