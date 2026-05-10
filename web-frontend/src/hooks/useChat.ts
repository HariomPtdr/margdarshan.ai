import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 as uuid } from "uuid";

import { sendChat } from "../lib/api";
import type { ChatResponse, Message } from "../lib/types";

export function useChat() {
  const { i18n } = useTranslation();
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [activeComplaintId, setActiveComplaintId] = useState<string | undefined>();
  const [needsLocationPin, setNeedsLocationPin] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  const reset = useCallback(() => {
    setSessionId(undefined);
    setActiveComplaintId(undefined);
    setNeedsLocationPin(false);
    setMessages([]);
    setLastResponse(null);
  }, []);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      setBusy(true);

      const userMsg: Message = {
        id: uuid(),
        role: "user",
        content: text,
        timestamp: Date.now(),
      };
      setMessages((m) => [...m, userMsg]);

      try {
        const resp = await sendChat(text, sessionId, i18n.language);
        setSessionId(resp.session_id);
        if (resp.complaint_id) setActiveComplaintId(resp.complaint_id);
        setNeedsLocationPin(resp.needs_location_pin);
        setLastResponse(resp);

        const botMsg: Message = {
          id: uuid(),
          role: "assistant",
          content: resp.reply,
          timestamp: Date.now(),
        };
        setMessages((m) => [...m, botMsg]);
      } catch (e: any) {
        const errMsg: Message = {
          id: uuid(),
          role: "assistant",
          content: e?.message || "Server error. Please try again.",
          timestamp: Date.now(),
        };
        setMessages((m) => [...m, errMsg]);
      } finally {
        setBusy(false);
      }
    },
    [sessionId, i18n.language],
  );

  return {
    sessionId,
    setSessionId,
    activeComplaintId,
    setActiveComplaintId,
    needsLocationPin,
    setNeedsLocationPin,
    messages,
    setMessages,
    busy,
    lastResponse,
    send,
    reset,
  };
}
