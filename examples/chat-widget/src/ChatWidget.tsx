import React, { useEffect, useRef, useState } from "react";
import type { ChatWidgetProps, Message } from "./types";
import { BotIcon, SendIcon, UserIcon, XIcon } from "./icons";
import { getDictionary } from "./i18n";
import { getOrCreateSessionId, getStorageScope, loadMessages, saveMessages } from "./storage";
import { useChatStream } from "./useChatStream";

import "./styles.css";

/**
 * ChatWidget：开箱即用客服聊天面板。
 *
 * 接入（业务方）：
 *   import { ChatWidget } from "customer-helpmesh-agent-chat-widget";
 *   <ChatWidget endpoint="/api/agent/chat" userId={session.userId} onClose={...} />
 *
 * 改样式：覆盖同 class 名（CSS specificity 高于 styles.css）。
 * 替换组件：用 useChatStream + 自写 UI。
 */
export function ChatWidget({
  endpoint,
  userId = null,
  onClose,
  locale = "zh",
  storageScope = "agent",
}: ChatWidgetProps) {
  const t = getDictionary(locale);
  const scope = getStorageScope(userId, storageScope);
  const [threadId, setThreadId] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1) 初始化 threadId + 历史消息（welcome 或 localStorage）
  useEffect(() => {
    const sid = getOrCreateSessionId(scope);
    setThreadId(sid);
    const stored = loadMessages(scope, sid);
    if (stored.length > 0) {
      setLocalMessages(stored);
    } else {
      setLocalMessages([
        { id: "welcome", role: "agent", content: t.welcomeMessage, timestamp: new Date() },
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope, t.welcomeMessage]);

  // 2) SSE 流
  const { messages: streamMessages, isTyping, send } = useChatStream({ endpoint, userId, threadId });

  // 3) 合并：本地消息（welcome + 历史） + 流式消息（本次对话 user + agent）
  const allMessages = [...localMessages, ...streamMessages];

  // 4) 持久化
  useEffect(() => {
    if (!threadId || allMessages.length === 0) return;
    saveMessages(scope, threadId, allMessages);
  }, [threadId, scope, allMessages]);

  // 5) 自动滚到底
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [allMessages, isTyping]);

  const handleSend = async () => {
    if (!inputValue.trim() || !threadId) return;
    const text = inputValue;
    setInputValue("");
    await send(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="ca-cw flex flex-col w-full h-full bg-white dark:bg-zinc-900 rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-zinc-800">
      <div className="ca-cw-header flex items-center justify-between px-4 py-3 bg-blue-600 text-white">
        <div className="flex items-center gap-2">
          <BotIcon className="w-5 h-5" />
          <span className="font-medium">{t.title}</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="ca-cw-close p-1 hover:bg-blue-700 rounded-md transition-colors" aria-label="Close">
            <XIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="ca-cw-list flex-1 overflow-y-auto p-4 space-y-4">
        {allMessages.map((msg) => (
          <div key={msg.id} className={`ca-cw-msg flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`ca-cw-row flex max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"} gap-2`}>
              <div className="flex-shrink-0 mt-1">
                {msg.role === "user" ? (
                  <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                    <UserIcon className="w-4 h-4" />
                  </div>
                ) : (
                  <div className="w-8 h-8 bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-300 rounded-full flex items-center justify-center">
                    <BotIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
              <div
                className={`ca-cw-bubble px-4 py-2 rounded-2xl ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm"
                    : "bg-gray-100 dark:bg-zinc-800 text-gray-800 dark:text-zinc-200 rounded-tl-sm"
                }`}
              >
                <p className="ca-cw-text text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                <span className={`ca-cw-time text-[10px] block mt-1 ${msg.role === "user" ? "text-blue-200" : "text-gray-400"}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="ca-cw-typing flex justify-start">
            <div className="ca-cw-row flex max-w-[80%] flex-row gap-2">
              <div className="flex-shrink-0 mt-1">
                <div className="w-8 h-8 bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-300 rounded-full flex items-center justify-center">
                  <BotIcon className="w-4 h-4" />
                </div>
              </div>
              <div className="ca-cw-bubble px-4 py-3 rounded-2xl bg-gray-100 dark:bg-zinc-800 rounded-tl-sm flex items-center gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ca-cw-input p-3 border-t border-gray-100 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/50">
        <div className="flex items-center gap-2 bg-white dark:bg-zinc-800 rounded-full border border-gray-200 dark:border-zinc-700 px-3 py-2 shadow-sm focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.inputPlaceholder}
            disabled={!threadId}
            className="flex-1 bg-transparent border-none focus:outline-none text-sm px-1 dark:text-white"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || !threadId}
            className="p-1.5 bg-blue-600 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
          >
            <SendIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export { useChatStream } from "./useChatStream";
export type * from "./types";