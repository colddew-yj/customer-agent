// Next.js BFF：把自家 cookie 换成 agent 认识的 access token，调 agent /chat
// 路径：app/api/agent/chat/route.ts

import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL ?? "http://customer-helpmesh-agent:8000";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { message, sessionId } = body;

  const userToken = req.cookies.get("app_session")?.value ?? "";
  const userId = req.cookies.get("app_user_id")?.value ?? "";

  const upstream = await fetch(`${AGENT_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: userToken ? `Bearer ${userToken}` : "",
      "X-User-Id": userId,
      "X-Thread-Id": sessionId ?? "default",
    },
    body: JSON.stringify({ message, user_id: userId || undefined }),
  });

  return new NextResponse(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}