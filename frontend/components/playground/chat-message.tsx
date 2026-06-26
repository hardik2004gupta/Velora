"use client";

import { Copy, Check, RotateCcw, User, Sparkles, AlertCircle } from "lucide-react";
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "./markdown-renderer";
import type { ConversationMessage } from "@/types";

interface ChatMessageProps {
  message: ConversationMessage;
  onRetry?: () => void;
}

function StreamingCursor() {
  return (
    <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-velora-400 align-middle" />
  );
}

export function ChatMessageBubble({ message, onRetry }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  const copyContent = useCallback(async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  return (
    <div
      className={cn(
        "group flex gap-3 px-2 py-3",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-velora-500/20 text-velora-400"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? (
          <User className="h-3.5 w-3.5" />
        ) : (
          <Sparkles className="h-3.5 w-3.5" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn("flex max-w-[80%] flex-col gap-1", isUser && "items-end")}>
        {/* Provider label */}
        {isAssistant && message.provider && (
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">
            {message.provider} · {message.model}
          </span>
        )}

        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm",
            isUser
              ? "bg-velora-500/15 text-foreground"
              : "bg-card border border-border/50 text-foreground",
            message.error && "border-destructive/50 bg-destructive/5"
          )}
        >
          {message.error ? (
            <div className="flex items-start gap-2 text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{message.error}</span>
            </div>
          ) : isAssistant ? (
            <>
              <MarkdownRenderer content={message.content} />
              {message.isStreaming && <StreamingCursor />}
            </>
          ) : (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          )}
        </div>

        {/* Timestamp + actions */}
        <div
          className={cn(
            "flex items-center gap-2 text-[10px] text-muted-foreground/50",
            isUser ? "flex-row-reverse" : "flex-row"
          )}
        >
          <span>
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>

          {isAssistant && !message.isStreaming && message.content && !message.error && (
            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              <button
                onClick={copyContent}
                className="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-muted"
                title="Copy response"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-emerald-400" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </button>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-muted"
                  title="Retry"
                >
                  <RotateCcw className="h-3 w-3" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
