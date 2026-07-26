export type MessageRole = "user" | "agent";

export type Message = {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
};

export type Locale = "en" | "zh";

export type ChatWidgetProps = {
  endpoint: string;
  userId?: string | null;
  onClose?: () => void;
  locale?: Locale;
  storageScope?: string;
};

export type UseChatStreamOptions = {
  endpoint: string;
  userId?: string | null;
  threadId: string;
};

export type UseChatStreamResult = {
  messages: Message[];
  isTyping: boolean;
  error: string | null;
  send: (text: string) => Promise<void>;
  reset: () => void;
};