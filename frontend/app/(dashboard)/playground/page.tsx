"use client";

import {
  useRef,
  useEffect,
  useState,
  useCallback,
  KeyboardEvent,
} from "react";
import { Send, Square, Trash2, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { streamChat } from "@/lib/streaming";
import { usePlaygroundStore } from "@/store/playground";
import { ChatMessageBubble } from "@/components/playground/chat-message";
import { StrategySelector } from "@/components/playground/strategy-selector";
import { RoutingDecisionCard } from "@/components/playground/routing-decision-card";
import type { ConversationMessage, RoutingDecision } from "@/types";

let _idCounter = 0;
function nextId() {
  return `msg-${++_idCounter}-${Date.now()}`;
}

export default function PlaygroundPage() {
  const {
    messages,
    isStreaming,
    selectedStrategy,
    manualProvider,
    selectedModel,
    conversationId,
    addMessage,
    updateLastAssistantMessage,
    setError,
    setStreaming,
    setStrategy,
    setManualProvider,
    setModel,
    clearConversation,
  } = usePlaygroundStore();

  const [input, setInput] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [input]);

  const sendMessage = useCallback(async () => {
    const content = input.trim();
    if (!content || isStreaming) return;

    setInput("");

    const history = messages.map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    }));

    const userMsg: ConversationMessage = {
      id: nextId(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    addMessage(userMsg);

    const assistantMsg: ConversationMessage = {
      id: nextId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };
    addMessage(assistantMsg);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    let accumulated = "";
    let finalRoutingDecision: RoutingDecision | undefined;

    try {
      const stream = streamChat(
        {
          messages: [...history, { role: "user", content }],
          routing_strategy: selectedStrategy,
          ...(selectedStrategy === "manual" ? { manual_provider: manualProvider } : {}),
          model: selectedModel || undefined,
          max_tokens: 2048,
          temperature: 0.7,
          conversation_id: conversationId,
        },
        controller.signal
      );

      for await (const chunk of stream) {
        if (chunk.type === "delta" && chunk.content) {
          accumulated += chunk.content;
          updateLastAssistantMessage(accumulated, false);
        } else if (chunk.type === "done") {
          finalRoutingDecision = chunk.routing_decision;
          updateLastAssistantMessage(accumulated, true, finalRoutingDecision, chunk.cache_hit, chunk.fallback_provider);
        } else if (chunk.type === "error") {
          setError(chunk.message ?? "An error occurred.");
          return;
        }
      }

      updateLastAssistantMessage(accumulated, true, finalRoutingDecision);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        updateLastAssistantMessage(accumulated, true);
      } else {
        const msg = err instanceof Error ? err.message : "Something went wrong.";
        setError(msg);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [
    input,
    isStreaming,
    messages,
    selectedStrategy,
    manualProvider,
    selectedModel,
    conversationId,
    addMessage,
    updateLastAssistantMessage,
    setError,
    setStreaming,
  ]);

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const retryLast = useCallback(() => {
    const lastUserIdx = [...messages].reverse().findIndex((m) => m.role === "user");
    if (lastUserIdx === -1) return;
    const lastUser = messages[messages.length - 1 - lastUserIdx];
    setInput(lastUser.content);
    usePlaygroundStore.setState((s) => ({
      messages: s.messages.filter((_, i) => i < s.messages.length - 1),
    }));
  }, [messages]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage]
  );

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border/50 px-6 py-3">
        <div>
          <h1 className="text-lg font-semibold">AI Playground</h1>
          <p className="text-xs text-muted-foreground">
            Choose a routing strategy and start chatting
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StrategySelector
            strategy={selectedStrategy}
            manualProvider={manualProvider}
            onStrategyChange={setStrategy}
            onManualProviderChange={setManualProvider}
            disabled={isStreaming}
          />
          {!isEmpty && (
            <button
              onClick={clearConversation}
              disabled={isStreaming}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40"
              title="Clear conversation"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <EmptyState strategy={selectedStrategy} onSuggestion={setInput} />
        ) : (
          <div className="mx-auto max-w-3xl px-4 py-6">
            {messages.map((msg, i) => (
              <div key={msg.id}>
                <ChatMessageBubble
                  message={msg}
                  onRetry={
                    msg.role === "assistant" && !isStreaming && i === messages.length - 1
                      ? retryLast
                      : undefined
                  }
                />
                {msg.role === "assistant" && !msg.isStreaming && msg.routing_decision && (
                  <RoutingDecisionCard decision={msg.routing_decision} />
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border/50 bg-background px-4 py-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-3 rounded-xl border border-border/50 bg-card px-4 py-3 shadow-sm focus-within:border-velora-500/50">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isStreaming
                  ? "Generating…"
                  : "Message Velora… (Enter to send, Shift+Enter for newline)"
              }
              disabled={isStreaming}
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm leading-relaxed text-foreground placeholder-muted-foreground/60 focus:outline-none disabled:opacity-50"
              style={{ maxHeight: "200px" }}
            />
            {isStreaming ? (
              <button
                onClick={stopGeneration}
                className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20"
                title="Stop generation"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
              </button>
            ) : (
              <button
                onClick={sendMessage}
                disabled={!input.trim()}
                className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-velora-500 text-white hover:bg-velora-600 disabled:opacity-30"
                title="Send message"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <p className="mt-2 text-center text-[10px] text-muted-foreground/40">
            Responses may be inaccurate. Always verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

const SUGGESTIONS: Record<string, string[]> = {
  auto: [
    "Explain how transformer attention works",
    "Write a Python async HTTP client",
    "What is the difference between TCP and UDP?",
    "Summarise the CAP theorem",
  ],
  cheapest: [
    "Write a regex to validate email addresses",
    "Explain REST vs GraphQL in one paragraph",
    "Give me 5 names for a developer tool startup",
    "What is the time complexity of quicksort?",
  ],
  fastest: [
    "Translate 'Hello, world!' to French",
    "What is 17 × 19?",
    "One sentence: what is idempotency?",
    "Fix this: console.log('Hello World)",
  ],
  quality: [
    "Analyse the trade-offs of microservices vs monolith",
    "Write a detailed explanation of gradient descent",
    "What makes a great API design? Give examples.",
    "Compare React 18 and React 19 with code samples",
  ],
  manual: [
    "Explain how transformer attention works",
    "Write a Python async HTTP client",
    "Compare REST and GraphQL",
    "What is the CAP theorem?",
  ],
};

function EmptyState({
  strategy,
  onSuggestion,
}: {
  strategy: string;
  onSuggestion: (s: string) => void;
}) {
  const suggestions = SUGGESTIONS[strategy] ?? SUGGESTIONS.auto;
  const label = strategy.charAt(0).toUpperCase() + strategy.slice(1);
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 px-4 py-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-velora-500/10">
        <MessageSquare className="h-7 w-7 text-velora-400" />
      </div>
      <div className="space-y-1.5">
        <h2 className="text-xl font-semibold">Start a conversation</h2>
        <p className="text-sm text-muted-foreground">
          Using{" "}
          <span className="text-foreground font-medium">{label}</span> routing —
          Velora will select the best provider automatically.
        </p>
      </div>
      <div className="grid w-full max-w-xl grid-cols-2 gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="rounded-xl border border-border/50 bg-card px-4 py-3 text-left text-xs text-muted-foreground transition-colors hover:border-velora-500/30 hover:bg-velora-500/5 hover:text-foreground"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
