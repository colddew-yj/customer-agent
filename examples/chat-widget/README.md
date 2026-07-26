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