import { useState } from "react";
import { ChatWidget } from "../../src/ChatWidget";

/**
 * 业务方接入示例：右下角悬浮气泡。
 * 真实场景：业务方把 <ChatLauncher /> 贴到自家网站 body 末尾
 * （Next.js _app.tsx / Vue App.vue / 普通 index.html 末尾 div）。
 */
function ChatLauncher() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* 悬浮气泡（默认关闭状态） */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          aria-label="打开客服"
          className="fixed bottom-6 right-6 w-16 h-16 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-2xl flex items-center justify-center transition-colors z-50"
        >
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
            <path d="M3 4l18 8-18 8 4-8z" />
          </svg>
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-red-500" />
        </button>
      )}

      {/* 展开的聊天面板 */}
      {open && (
        <div className="fixed bottom-6 right-6 w-[380px] h-[600px] bg-white dark:bg-zinc-900 rounded-xl shadow-2xl border border-gray-200 dark:border-zinc-800 overflow-hidden z-50 flex flex-col">
          <ChatWidget
            endpoint="http://localhost:8000/chat"
            userId="demo-1"
            onClose={() => setOpen(false)}
            locale="zh"
          />
        </div>
      )}
    </>
  );
}

export function App() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          customer-agent chat-widget demo
        </h1>
        <p className="text-gray-600 dark:text-zinc-400 mb-2">
          右下角蓝色圆形按钮是悬浮气泡。点击展开聊天面板。
        </p>
        <p className="text-gray-600 dark:text-zinc-400 text-sm">
          业务方集成：把 <code className="px-1 py-0.5 bg-gray-200 dark:bg-zinc-800 rounded">&lt;ChatLauncher /&gt;</code> 贴到自己网站 body 末尾。
        </p>
        <p className="text-gray-600 dark:text-zinc-400 text-sm mt-4">
          后端: <code>http://localhost:8000</code>（先跑 <code>python -m agent.cli serve</code>）
        </p>
      </div>
      <ChatLauncher />
    </div>
  );
}
