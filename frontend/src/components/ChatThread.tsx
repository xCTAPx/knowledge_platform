import { type ChatMessage } from "../lib/chats";
import "./ChatThread.css";

export function ChatThread({ messages, busy }: { messages: ChatMessage[]; busy: boolean }) {
  if (!messages.length) {
    return <p className="muted chat-empty">Ask about your notes and files. Past chats stay in the list.</p>;
  }
  const last = messages.at(-1);
  return (
    <ol className="chat-thread">
      {messages.map((msg) => (
        <li key={msg.id} className={msg.role === "user" ? "msg user" : "msg assistant"}>
          <p className={busy && msg.id === last?.id && msg.role === "assistant" ? "streaming" : undefined}>{msg.text}</p>
        </li>
      ))}
    </ol>
  );
}
