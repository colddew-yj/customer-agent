# customer-agent-chat-widget

开箱即用客服聊天面板，与 [customer-agent](https://github.com/colddew-yj/customer-agent) 后端 SSE 对接。

源参考自 hachey 项目 `components/customer-service/chat-panel.tsx`，交互逻辑相同，样式可改 / 组件可替换。

## 安装

```bash
# copy 到业务方项目（或 npm install 后 publish）
cp -r src/ <your-project>/src/chat-widget/

# 业务方 BFF 需有 /api/agent/chat 路由（参考 examples/bff/nextjs/route.ts）
```

## 用法 1：开箱即用

```tsx
import { ChatWidget } from "./chat-widget";

<ChatWidget
  endpoint="/api/agent/chat"
  userId={session.userId}
  onClose={() => setOpen(false)}
  locale="zh"
/>
```

## 用法 2：换样式

业务方在自己 CSS 里覆盖同 class 名（CSS specificity 高于 `src/styles.css`）：

```css
.ca-cw-header { background-color: #ff6b6b; }
.ca-cw-bubble { border-radius: 4px; }
```

所有 class 都有 `ca-cw-` 前缀避免冲突。

## 用法 3：换组件（自写 UI）

不要 ChatWidget，用 `useChatStream`自己接：

```tsx
import { useChatStream } from "./chat-widget";

function MyCustomChat() {
  const { messages, send, isTyping } = useChatStream({
    endpoint: "/api/agent/chat",
    userId: "123",
    threadId: "abc",
  });
  return (
    <div>
      {messages.map((m) => <p key={m.id}>{m.role}: {m.content}</p>)}
      <button onClick={() => send("hello")}>send</button>
    </div>
  );
}
```


## 集成到业务方现有项目（4 步）

### React / Vite

```bash
cp -r src/ <your-project>/src/chat-widget/
```

```tsx
// <your-project>/src/main.tsx（贴一次即可，业务方网站每个页面都可用）
import { ChatLauncher } from "./chat-widget/demo/src/App";  // 复制 demo/src/App.tsx 改名 ChatLauncher
// 或自己写一个 ChatLauncher 组件（参考 demo/src/App.tsx 的 60 行）
```

### Next.js（App Router）

```bash
cp -r src/ <your-project>/components/chat-widget/
```

```tsx
// app/layout.tsx
import { ChatLauncher } from "@/components/chat-widget/demo/src/App";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html><body>
      {children}
      <ChatLauncher />   {/* 全站右下角悬浮气泡 */}
    </body></html>
  );
}
```

```tsx
// app/api/agent/chat/route.ts（BFF 转发到 agent，详见下面"BFF 端点契约"）
import { NextRequest, NextResponse } from "next/server";
const AGENT = process.env.AGENT_URL ?? "http://localhost:8000";
export async function POST(req: NextRequest) {
  const body = await req.json();
  const token = req.cookies.get("app_session")?.value ?? "";
  const userId = req.cookies.get("app_user_id")?.value ?? "";
  const upstream = await fetch(`${AGENT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}`, "X-User-Id": userId },
    body: JSON.stringify(body),
  });
  return new NextResponse(upstream.body, { headers: { "Content-Type": "text/event-stream" } });
}
```

### Vue / Svelte / Solid / 原生 JS

只复用 `useChatStream.ts` 思路（fetch + reader + decoder + 帧切分）。SSE 部分 30 行可移植，业务方按自家框架重写 UI hook。

## ChatWidget 内部 class 对照表（业务方改样式用）

所有元素都有 `ca-cw-` 前缀避免冲突，CSS specificity 高于 `src/styles.css` 即可覆盖。

| Class | 元素 | 业务方常改 |
|---|---|---|
| `.ca-cw` | 根容器 | 字体 family（默认系统字体） |
| `.ca-cw-header` | 顶部蓝条 | 背景色（替换成品牌色） |
| `.ca-cw-close` | X 关闭按钮 | hover 颜色 |
| `.ca-cw-list` | 消息列表区 | 背景色 / 滚动条样式 |
| `.ca-cw-msg` | 单条消息 | — |
| `.ca-cw-row` | 头像 + 气泡一行 | gap 间距 |
| `.ca-cw-bubble` | 聊天气泡 | 圆角 / 内边距 / 字体 |
| `.ca-cw-text` | 气泡内文字 | 字号 / 颜色 |
| `.ca-cw-time` | 时间戳 | 字号 / 颜色 |
| `.ca-cw-typing` | 打字点动画容器 | — |
| `.ca-cw-input` | 输入区 | 背景色 / 边框 |

**改色示例**（保持整体风格，只换品牌色）：

```css
.ca-cw-header { background-color: #10b981; }   /* 绿（替换蓝 #2563eb） */
```

用户气泡没单独 class —— 用户气泡在 `.ca-cw-row > div:nth-child(2)`（flex 容器第二个子元素），CSS selector：

```css
.ca-cw-row > div + div > .ca-cw-bubble { background-color: #10b981; }
```

## 替换 storage（接业务方自家 auth state）

默认走 localStorage（`cs_session_id_<scope>` / `cs_messages_<scope>_<sessionId>`）。业务方已有自家 auth 时，**改 `src/storage.ts`**：

```ts
// src/storage.ts 替换为：调业务方 API
export function getOrCreateSessionId(scope: string): string {
  // 例：返回业务方自家 sessionId，从自家 auth state 取
  return useAuthStore.getState().sessionId;  // Zustand 例子
}

export function loadMessages(scope: string, sessionId: string): Message[] {
  // 例：从业务方后端拉历史
  return useChatStore.getState().messages;
}

export function saveMessages(scope: string, sessionId: string, messages: Message[]): void {
  // 例：业务方后端保存
  api.saveMessages(messages);
}
```

`useChatStream.ts` 只调这 3 个函数，**改 storage 不动 stream 逻辑**。

## BFF 端点契约

`POST /api/agent/chat`（业务方实现，BFF 转发到 agent `/chat`）：

```bash
curl -X POST http://localhost:3000/api/agent/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 123" \
  -H "Authorization: Bearer <user-token>" \
  -d '{"message":"怎么充值"}'
```

响应 SSE 帧：

```
data: {"type":"token","content":"支付"}\n\n
data: {"type":"token","content":"宝"}\n\n
data: [DONE]\n\n
```

参考实现：[`examples/bff/nextjs/route.ts`](../../examples/bff/nextjs/route.ts)

## License

MIT（同主仓）