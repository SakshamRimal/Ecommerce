import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  MessageSquarePlus,
  Send,
  Sparkles,
  User as UserIcon,
  X,
} from "lucide-react";
import { api, ApiError } from "../../lib/api/client";
import { qk } from "../../lib/query-keys";
import { useAuthStore } from "../../stores/auth-store";
import { useUiStore } from "../../stores/ui-store";
import { Button } from "../ui/Primitives";

const STARTER_PROMPTS = [
  "What products do you currently have in stock?",
  "Do you have any running shoes under $150?",
  "Tell me about the Nike Air Max and check its stock",
];

/**
 * Lightweight inline formatter so **bold** and *italic* segments render nicely
 * inside assistant replies without raw markdown asterisks.
 */
function renderFormattedLine(line: string): React.ReactNode[] {
  const parts = line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return (
        <strong key={idx} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return (
        <em key={idx} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

function FormattedMessage({ content }: { content: string }) {
  const lines = content.split("\n");
  return (
    <div className="space-y-1.5">
      {lines.map((line, idx) => {
        if (!line.trim()) {
          return <div key={idx} className="h-1" />;
        }
        return (
          <p key={idx} className="leading-relaxed">
            {renderFormattedLine(line)}
          </p>
        );
      })}
    </div>
  );
}

export function AssistantDrawer() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { status, user } = useAuthStore();
  const {
    chatDrawerOpen,
    setChatDrawerOpen,
    chatPrompt,
    clearChatPrompt,
    addToast,
  } = useUiStore();

  const [draft, setDraft] = useState("");
  const [localMessages, setLocalMessages] = useState<
    { id: string; role: "user" | "assistant"; content: string }[]
  >([]);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (chatDrawerOpen && chatPrompt) {
      setDraft(chatPrompt);
      clearChatPrompt();
    }
  }, [chatDrawerOpen, chatPrompt, clearChatPrompt]);

  const { data: historyData } = useQuery({
    queryKey: qk.chatHistory(),
    queryFn: () => api.chat.history(50),
    enabled: chatDrawerOpen && status === "authenticated",
  });

  useEffect(() => {
    if (historyData?.messages) {
      setLocalMessages(
        historyData.messages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        })),
      );
    }
  }, [historyData]);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const timer = setInterval(() => {
      setCooldownSeconds((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [localMessages, chatDrawerOpen]);

  const sendMutation = useMutation({
    mutationFn: (message: string) => api.chat.send(message),
    onMutate: (message) => {
      setErrorBanner(null);
      const optimisticId = `temp-${Date.now()}`;
      setLocalMessages((prev) => [
        ...prev,
        { id: optimisticId, role: "user", content: message },
      ]);
      setDraft("");
    },
    onSuccess: (res) => {
      setLocalMessages((prev) => [
        ...prev,
        {
          id: `reply-${Date.now()}`,
          role: "assistant",
          content: res.reply,
        },
      ]);
      queryClient.invalidateQueries({ queryKey: qk.chatHistory() });
    },
    onError: (err: Error, originalMessage) => {
      setDraft(originalMessage);
      if (err instanceof ApiError && err.status === 429) {
        setCooldownSeconds(30);
        setErrorBanner(
          "Rate limit reached (10 messages/minute). Please wait a moment before sending again.",
        );
      } else {
        setErrorBanner(err.message);
      }
    },
  });

  const newChatMutation = useMutation({
    mutationFn: () => api.chat.clearHistory(),
    onSuccess: () => {
      setLocalMessages([]);
      setErrorBanner(null);
      setDraft("");
      queryClient.setQueryData(qk.chatHistory(), { messages: [] });
      addToast({
        title: "Started a new chat",
        description: "Previous conversation history has been cleared.",
        tone: "info",
      });
      inputRef.current?.focus();
    },
    onError: () => {
      setLocalMessages([]);
      setErrorBanner(null);
    },
  });

  if (!chatDrawerOpen) return null;

  const handleSend = (text?: string) => {
    const msg = (text ?? draft).trim();
    if (!msg || sendMutation.isPending || cooldownSeconds > 0) return;
    sendMutation.mutate(msg);
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-label="AI Shopping Assistant"
    >
      <div
        className="fixed inset-0 bg-slate-950/50 backdrop-blur-xs"
        onClick={() => setChatDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="flex w-screen max-w-md flex-col bg-white shadow-2xl dark:bg-slate-900">
          {/* Header with New Chat button */}
          <div className="flex items-center justify-between border-b border-slate-200 bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-4 text-white dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold sm:text-base">
                  AI Shopping Concierge
                </h2>
                <p className="text-[11px] text-indigo-100">
                  Live catalog search &amp; stock verification
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {status === "authenticated" && (
                <button
                  type="button"
                  onClick={() => newChatMutation.mutate()}
                  disabled={newChatMutation.isPending || sendMutation.isPending}
                  title="Start a new chat conversation"
                  className="inline-flex items-center gap-1.5 rounded-xl bg-white/15 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/25 disabled:opacity-50 cursor-pointer"
                >
                  <MessageSquarePlus className="h-3.5 w-3.5" />
                  <span>New Chat</span>
                </button>
              )}
              <button
                type="button"
                aria-label="Close AI assistant"
                onClick={() => setChatDrawerOpen(false)}
                className="rounded-lg p-1.5 text-white/80 hover:bg-white/10 hover:text-white cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {status !== "authenticated" ? (
            <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                Sign in to chat with the AI Concierge
              </h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Your conversation history and personalized catalog recommendations
                are tied to your account.
              </p>
              <Button
                className="mt-5"
                onClick={() => {
                  setChatDrawerOpen(false);
                  navigate("/login");
                }}
              >
                Sign In
              </Button>
            </div>
          ) : (
            <>
              <div
                ref={logRef}
                role="log"
                aria-live="polite"
                className="flex-1 space-y-4 overflow-y-auto p-5"
              >
                {localMessages.length === 0 && (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4 text-sm text-slate-700 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-slate-200">
                      <p className="font-semibold text-indigo-950 dark:text-indigo-200">
                        Hi{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}! 👋
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                        I&apos;m connected directly to the live store catalog. Ask me
                        to search products, filter by price, or check real-time
                        warehouse stock.
                      </p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        Suggested Questions
                      </p>
                      <div className="flex flex-col gap-2">
                        {STARTER_PROMPTS.map((prompt) => (
                          <button
                            key={prompt}
                            type="button"
                            onClick={() => handleSend(prompt)}
                            className="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs font-medium text-slate-700 transition hover:border-indigo-400 hover:bg-indigo-50/40 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-200 cursor-pointer"
                          >
                            &ldquo;{prompt}&rdquo;
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {localMessages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex items-start gap-2.5 ${
                      m.role === "user" ? "flex-row-reverse" : ""
                    }`}
                  >
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                      }`}
                    >
                      {m.role === "user" ? (
                        <UserIcon className="h-3.5 w-3.5" />
                      ) : (
                        <Bot className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <div
                      className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-sm ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
                      }`}
                    >
                      <FormattedMessage content={m.content} />
                    </div>
                  </div>
                ))}

                {sendMutation.isPending && (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="h-2 w-2 animate-ping rounded-full bg-indigo-600" />
                    Checking live catalog…
                  </div>
                )}

                {errorBanner && (
                  <div
                    role="alert"
                    className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
                  >
                    {errorBanner}
                  </div>
                )}
              </div>

              <div className="border-t border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-900">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                  className="space-y-2"
                >
                  <label htmlFor="chat-composer" className="sr-only">
                    Ask the shopping assistant
                  </label>
                  <div className="flex gap-2">
                    <textarea
                      ref={inputRef}
                      id="chat-composer"
                      rows={2}
                      maxLength={1000}
                      value={draft}
                      disabled={sendMutation.isPending || cooldownSeconds > 0}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSend();
                        }
                      }}
                      placeholder={
                        cooldownSeconds > 0
                          ? `Cooldown active (${cooldownSeconds}s)…`
                          : "Ask about products, prices, or live stock…"
                      }
                      className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                    />
                    <Button
                      type="submit"
                      disabled={
                        !draft.trim() ||
                        sendMutation.isPending ||
                        cooldownSeconds > 0
                      }
                      loading={sendMutation.isPending}
                      aria-label="Send message"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Press Enter to send · Click &ldquo;New Chat&rdquo; to reset</span>
                    <span>{draft.length}/1000</span>
                  </div>
                </form>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
