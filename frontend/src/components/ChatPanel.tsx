import { FormEvent } from "react";
import { type Chat, type ChatMessage } from "../lib/chats";
import { AskBox } from "./AskBox";
import { ChatList } from "./ChatList";
import { ChatThread } from "./ChatThread";
import "./ChatPanel.css";

export function ChatPanel({
  chats,
  messages,
  activeId,
  value,
  busy,
  locked,
  error,
  canNew,
  onSelect,
  onNew,
  onRename,
  onRemove,
  onChange,
  onSubmit,
}: {
  chats: Chat[];
  messages: ChatMessage[];
  activeId: number | null;
  value: string;
  busy: boolean;
  locked: boolean;
  error: string;
  canNew: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
  onRename: (id: number, title: string) => void;
  onRemove: (id: number) => void;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <section className="chats">
      <h2>Chat</h2>
      <ChatList
        chats={chats}
        activeId={activeId}
        canNew={canNew}
        onSelect={onSelect}
        onNew={onNew}
        onRename={onRename}
        onRemove={onRemove}
      />
      <div className="chat-main">
        <ChatThread messages={messages} busy={busy} />
        <AskBox value={value} busy={busy} locked={locked} error={error} onChange={onChange} onSubmit={onSubmit} />
      </div>
    </section>
  );
}
