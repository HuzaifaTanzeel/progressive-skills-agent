"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { SkillBadge } from "@/components/SkillBadge";
import {
  fetchSkillTiers,
  sendChat,
  type SkillTier,
} from "@/lib/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  skillUsed?: string | null;
};

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [skillTiers, setSkillTiers] = useState<Record<string, SkillTier>>(
    {},
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void fetchSkillTiers().then(setSkillTiers);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setInput("");
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendChat({
        message: text,
        user_id: "demo_user",
        session_id: sessionId,
      });
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.response || "(empty response)",
          skillUsed: data.skill_used,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-ink">
      <header className="border-b border-ink-muted px-4 py-5 sm:px-6">
        <div className="mx-auto flex max-w-2xl flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-display text-2xl font-semibold tracking-tight text-sand sm:text-3xl">
              GovTech Skills Assistant
            </p>
            <p className="mt-1 text-sm text-sand-dim">
              Demo chat — progressive Agent Skills over Saudi civic workflows
            </p>
          </div>
          <nav className="flex gap-4 text-sm">
            <span className="text-teal-bright" aria-current="page">
              Chat
            </span>
            <Link
              href="/dashboard"
              className="text-sand-dim transition-colors hover:text-teal-bright"
            >
              Dashboard
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 sm:px-6">
        <div className="flex-1 space-y-4 overflow-y-auto py-6">
          {messages.length === 0 && !loading ? (
            <p className="text-sm text-sand-dim">
              Ask about iqama renewal, traffic violations, fee drafts, or
              appointment slots.
            </p>
          ) : null}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={
                msg.role === "user"
                  ? "ml-8 flex flex-col items-end gap-1.5"
                  : "mr-4 flex flex-col items-start gap-1.5"
              }
            >
              {msg.role === "assistant" && msg.skillUsed ? (
                <SkillBadge
                  skillName={msg.skillUsed}
                  tier={skillTiers[msg.skillUsed]}
                />
              ) : null}
              <div
                className={
                  msg.role === "user"
                    ? "rounded-2xl rounded-br-md bg-teal px-4 py-2.5 text-sm leading-relaxed text-ink"
                    : "rounded-2xl rounded-bl-md bg-ink-raised px-4 py-2.5 text-sm leading-relaxed text-sand whitespace-pre-wrap"
                }
              >
                {msg.content}
              </div>
            </div>
          ))}

          {loading ? (
            <div className="mr-4 flex flex-col items-start gap-1.5">
              <div className="rounded-2xl rounded-bl-md bg-ink-raised px-4 py-2.5 text-sm text-sand-dim">
                Thinking…
              </div>
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>

        {error ? (
          <p className="mb-3 text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}

        <form
          onSubmit={handleSubmit}
          className="sticky bottom-0 flex gap-2 border-t border-ink-muted bg-ink py-4"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message…"
            disabled={loading}
            className="min-w-0 flex-1 rounded-xl border border-ink-muted bg-ink-raised px-4 py-3 text-sm text-sand placeholder:text-sand-dim outline-none focus:border-teal disabled:opacity-50"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-teal px-5 py-3 text-sm font-semibold text-ink transition-colors hover:bg-teal-bright disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
