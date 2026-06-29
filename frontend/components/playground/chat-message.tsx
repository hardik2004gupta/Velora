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
    <span className="ml-0.5 inline-block h-[14px] w-0.5 animate-pulse rounded-full bg-velora-400 align-middle" />
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
        "group flex gap-3 px-1 py-2",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-[10px]",
          isUser
            ? "bg-velora-500/20 text-velora-400"
            : "bg-muted/80 text-muted-foreground border border-border/50"
        )}
      >
        {isUser ? (
          <User className="h-3 w-3" />
        ) : (
          <Sparkles className="h-3 w-3" />
        )}
      </div>

      {/* Content */}
      <div className={cn("flex max-w-[82%] flex-col gap-1", isUser && "items-end")}>
        {/* Provider label for assistant */}
        {isAssistant && message.provider && (
          <span className="text-[10px] font-mono text-muted-foreground/50 ml-0.5">
            {message.provider} &middot; {message.model}
          </span>
        )}

        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-velora-500/12 text-foreground"
              : "rounded-tl-sm border border-border/50 bg-card/80 text-foreground",
            message.error && "border-destructive/40 bg-destructive/5"
          )}
        >
          {message.error ? (
            <div className="flex items-start gap-2 text-xs text-destructive">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
              <span>{message.error}</span>
            </div>
          ) : isAssistant ? (
            <>
              <MarkdownRenderer content={message.content} />
              {message.isStreaming && <StreamingCursor />}
            </>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* Footer: timestamp + actions */}
        <div
          className={cn(
            "flex items-center gap-2 px-1",
            isUser ? "flex-row-reverse" : "flex-row"
          )}
        >
          <span className="text-[10px] text-muted-foreground/40">
            {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>

          {isAssistant && !message.isStreaming && message.content && !message.error && (
            <div className="flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
              <button
                onClick={copyContent}
                title="Copy response"
                className="flex h-5 w-5 items-center justify-center rounded text-muted-foreground/60 hover:bg-muted hover:text-foreground transition-colors"
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
                  title="Retry"
                  className="flex h-5 w-5 items-center justify-center rounded text-muted-foreground/60 hover:bg-muted hover:text-foreground transition-colors"
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
