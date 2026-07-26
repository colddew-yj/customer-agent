import { useCallback, useEffect, useRef, useState } from "react";
import type { Message, UseChatStreamOptions, UseChatStreamResult } from "./types";

/**
 * useChatStream：与 BFF SSE endpoint 对接消费 hook。
 * 帧格式（与 agent server.py /chat 一致）：
 *   data: {"type":"token","content":"..."}\n\n
 *   data: {"type":"sources","sources":[...]}\n\n
 *   data: [DONE]\n\n
 */
export function useChatStream(opts: UseChatStreamOptions): UseChatStreamResult {
  const { endpoint, userId } = opts;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };
    const agentId = `${Date.now()}_agent`;
    const agentPlaceholder: Message = {
      id: agentId,
      role: "agent",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, agentPlaceholder]);
    setIsTyping(true);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, user_id: userId ?? null }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        throw new Error(`Chat failed: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const evt of events) {
          const line = evt.trim();
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (payload === "[DONE]") continue;
          try {
            const data = JSON.parse(payload);
            if ((data.type === "token" || data.type === "chunk") && typeof data.content === "string") {
              setMessages((prev) =>
                prev.map((m) => (m.id === agentId ? { ...m, content: m.content + data.content } : m)),
              );
            }
          } catch {
            // skip malformed frame
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentId
              ? { ...m, content: m.content || "抱歉，AI 服务暂时不可用，请稍后再试。" }
              : m,
          ),
        );
      }
    } finally {
      setIsTyping(false);
      abortRef.current = null;
    }
  }, [endpoint, userId]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isTyping, error, send, reset };
}