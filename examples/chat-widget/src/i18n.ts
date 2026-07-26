import type { Locale } from "./types";

export type Dictionary = {
  title: string;
  welcomeMessage: string;
  inputPlaceholder: string;
  errorMessage: string;
};

const en: Dictionary = {
  title: "Customer Service",
  welcomeMessage: "Hi, I'm your customer service assistant. Ask me anything.",
  inputPlaceholder: "Type your question...",
  errorMessage: "Sorry, the AI service is temporarily unavailable. Please try again.",
};

const zh: Dictionary = {
  title: "客服助理",
  welcomeMessage: "你好，我是客服助理。有什么可以帮你？",
  inputPlaceholder: "输入你的问题...",
  errorMessage: "抱歉，AI 服务暂时不可用，请稍后再试。",
};

const dictionaries: Record<Locale, Dictionary> = { en, zh };

export function getDictionary(locale: Locale = "zh"): Dictionary {
  return dictionaries[locale] ?? dictionaries.zh;
}