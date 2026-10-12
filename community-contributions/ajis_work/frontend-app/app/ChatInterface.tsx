"use client";

import { useEffect, useRef, useState } from "react";

type Role = "user" | "assistant";
type ChatMessage = { role: Role; content: string };
type Provider = "openai" | "anthropic";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_CHAT_BACKEND_URL ?? "http://localhost:8000";

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<Provider>("openai");
  const [isStreaming, setIsStreaming] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || isStreaming) return;

    const nextMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ];
    setMessages(nextMessages);
    setInput("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          provider,
          messages: nextMessages
            .slice(0, -1) // don't send the empty placeholder we just added
            .map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Backend error: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const raw of events) {
          const line = raw.replace(/^data: /, "").trim();
          if (!line) continue;

          const payload = JSON.parse(line);
          if (payload.type === "token") {
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = {
                ...copy[copy.length - 1],
                content: copy[copy.length - 1].content + payload.text,
              };
              return copy;
            });
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = {
            role: "assistant",
            content: "Something went wrong reaching the model. Check that the backend is running.",
          };
          return copy;
        });
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  function stopStreaming() {
    abortRef.current?.abort();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex h-screen flex-col bg-[#14181c] text-[#ece9e3]">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-3">
        <span className="text-sm tracking-wide text-white/50">
          {provider === "openai" ? "GPT" : "Claude"}
        </span>
        <div className="flex gap-1 rounded-full border border-white/10 p-0.5">
          {(["openai", "anthropic"] as Provider[]).map((p) => (
            <button
              key={p}
              onClick={() => setProvider(p)}
              className={`rounded-full px-3 py-1 text-xs transition ${
                provider === p
                  ? "bg-[#c9a66b] text-[#14181c]"
                  : "text-white/50 hover:text-white/80"
              }`}
            >
              {p === "openai" ? "OpenAI" : "Anthropic"}
            </button>
          ))}
        </div>
      </header>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto flex max-w-2xl flex-col gap-6">
          {messages.length === 0 && (
            <p className="mt-24 text-center text-white/30">
              Say something to start the conversation.
            </p>
          )}

          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="self-end max-w-[80%] rounded-2xl bg-[#c9a66b] px-4 py-2 text-[#14181c]">
                {m.content}
              </div>
            ) : (
              <div
                key={i}
                className="max-w-[85%] border-l-2 border-[#5b8c87] pl-4 font-serif text-[17px] leading-relaxed text-[#ece9e3] whitespace-pre-wrap"
              >
                {m.content}
                {isStreaming && i === messages.length - 1 && (
                  <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-[#5b8c87] align-middle" />
                )}
              </div>
            )
          )}
          <div ref={scrollRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-white/10 px-6 py-4">
        <div className="mx-auto flex max-w-2xl items-end gap-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              autoResize();
            }}
            onKeyDown={handleKeyDown}
            placeholder="Message..."
            rows={1}
            className="max-h-[200px] flex-1 resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-[#ece9e3] placeholder-white/30 outline-none focus:border-[#c9a66b]/60"
          />
          {isStreaming ? (
            <button
              onClick={stopStreaming}
              className="rounded-xl bg-white/10 px-4 py-3 text-sm text-white/80 hover:bg-white/20"
            >
              Stop
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!input.trim()}
              className="rounded-xl bg-[#c9a66b] px-4 py-3 text-sm font-medium text-[#14181c] disabled:opacity-30"
            >
              Send
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
