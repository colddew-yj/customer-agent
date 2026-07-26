import type { Message } from "./types";

export function getStorageScope(userId: string | null | undefined, scope: string): string {
  return userId ? `${scope}_user_${userId}` : `${scope}_guest`;
}

export function getSessionIdKey(scope: string): string {
  return `cs_session_id_${scope}`;
}

export function getOrCreateSessionId(scope: string): string {
  if (typeof window === "undefined") return "";
  const key = getSessionIdKey(scope);
  let sid = window.localStorage.getItem(key);
  if (!sid) {
    sid = `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    window.localStorage.setItem(key, sid);
  }
  return sid;
}

export function getMessagesKey(scope: string, sessionId: string): string {
  return `cs_messages_${scope}_${sessionId}`;
}

export type StoredMessage = Omit<Message, "timestamp"> & { timestamp: string };

export function loadMessages(scope: string, sessionId: string): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(getMessagesKey(scope, sessionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredMessage[];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((m) => m && typeof m.id === "string" && typeof m.content === "string")
      .map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.timestamp),
      }));
  } catch {
    return [];
  }
}

export function saveMessages(scope: string, sessionId: string, messages: Message[]): void {
  if (typeof window === "undefined") return;
  const serialized: StoredMessage[] = messages.map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
    timestamp: m.timestamp.toISOString(),
  }));
  try {
    window.localStorage.setItem(getMessagesKey(scope, sessionId), JSON.stringify(serialized));
  } catch {
    // ignore quota / private mode
  }
}