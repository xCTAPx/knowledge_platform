import { FormEvent, useEffect, useRef, useState } from "react";
import { errMsg } from "../lib/files";
import { letterStream } from "../lib/stream";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  listMessages,
  renameConversation,
  sendMessage,
  type ChatMessage,
  type Conversation,
  type User,
} from "../services/api";

export function useChats(user: User | null) {
  const [chats, setChats] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const skipLoad = useRef(false);
  const draft = chats.find((chat) => !chat.message_count);

  useEffect(() => {
    if (!user) {
      setChats([]);
      setActiveId(null);
      setMessages([]);
      return;
    }
    listConversations()
      .then((items) => {
        setChats(items);
        setActiveId(items[0]?.id ?? null);
      })
      .catch(() => {
        setChats([]);
        setActiveId(null);
      });
  }, [user]);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    if (skipLoad.current) {
      skipLoad.current = false;
      return;
    }
    let gone = false;
    listMessages(activeId)
      .then((items) => {
        if (!gone) setMessages(items);
      })
      .catch(() => {
        if (!gone) setMessages([]);
      });
    return () => {
      gone = true;
    };
  }, [activeId]);

  async function newChat() {
    if (draft) {
      setActiveId(draft.id);
      return;
    }
    try {
      const chat = await createConversation();
      setChats((prev) => [chat, ...prev]);
      setActiveId(chat.id);
      setMessages([]);
      setError("");
    } catch (err) {
      setError(errMsg(err, "Could not start chat"));
    }
  }

  async function removeChat(id: number) {
    try {
      await deleteConversation(id);
      const next = chats.filter((chat) => chat.id !== id);
      setChats(next);
      if (id === activeId) setActiveId(next[0]?.id ?? null);
    } catch (err) {
      setError(errMsg(err, "Could not delete chat"));
    }
  }

  async function renameChat(id: number, title: string) {
    const next = title.trim();
    if (!next) return;
    try {
      const chat = await renameConversation(id, next);
      setChats((prev) => prev.map((item) => (item.id === id ? chat : item)));
    } catch (err) {
      setError(errMsg(err, "Could not rename chat"));
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = value.trim();
    if (!q || busy) return;
    setValue("");
    setError("");
    let chatId = activeId;
    try {
      if (!chatId) {
        const chat = await createConversation();
        skipLoad.current = true;
        setChats((prev) => [chat, ...prev]);
        setActiveId(chat.id);
        chatId = chat.id;
      }
      const asstId = -Date.now();
      setMessages((prev) => [
        ...prev,
        { id: asstId - 1, role: "user", text: q, created_at: "" },
        { id: asstId, role: "assistant", text: "", created_at: "" },
      ]);
      setChats((prev) =>
        prev.map((chat) => (chat.id === chatId ? { ...chat, title: chat.message_count ? chat.title : (q.split("\n")[0] ?? q), message_count: chat.message_count + 1 } : chat))
      );
      setBusy(true);
      const letters = letterStream((text) => {
        setMessages((prev) => prev.map((msg) => (msg.id === asstId ? { ...msg, text } : msg)));
      });
      try {
        await sendMessage(chatId, q, letters.push);
        await letters.end();
        const [items, chat] = await Promise.all([listMessages(chatId), getConversation(chatId)]);
        setMessages(items);
        setChats((prev) => prev.map((item) => (item.id === chatId ? chat : item)));
      } catch (err) {
        letters.stop();
        throw err;
      }
    } catch (err) {
      setError(errMsg(err, "Could not ask"));
    } finally {
      setBusy(false);
    }
  }

  return {
    chats,
    activeId,
    messages,
    setActiveId,
    value,
    setValue,
    error,
    busy,
    canNew: !draft,
    newChat,
    removeChat,
    renameChat,
    onSubmit,
  };
}
