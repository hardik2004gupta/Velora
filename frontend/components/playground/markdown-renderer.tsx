"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import rehypeHighlight from "rehype-highlight";
import { Copy, Check } from "lucide-react";
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";

// highlight.js dark theme
import "highlight.js/styles/github-dark.css";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={copy}
      className="absolute right-2 top-2 flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
    >
      {copied ? (
        <><Check className="h-3 w-3" /> Copied</>
      ) : (
        <><Copy className="h-3 w-3" /> Copy</>
      )}
    </button>
  );
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div
      className={cn(
        "prose prose-sm prose-invert max-w-none",
        // headings
        "prose-headings:font-semibold prose-headings:text-foreground",
        // inline code
        "prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:text-xs prose-code:text-velora-300 prose-code:before:content-none prose-code:after:content-none",
        // blockquote
        "prose-blockquote:border-l-velora-500 prose-blockquote:text-muted-foreground",
        // table
        "prose-table:text-sm prose-th:text-foreground prose-td:text-muted-foreground",
        // links
        "prose-a:text-velora-400 prose-a:no-underline hover:prose-a:underline",
        // paragraph
        "prose-p:text-foreground/90 prose-p:leading-relaxed",
        // lists
        "prose-li:text-foreground/90",
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize, rehypeHighlight]}
        components={{
          // Wrap pre/code in a relative container for the copy button
          pre({ children, ...props }) {
            const codeEl = (children as React.ReactElement)?.props;
            const codeText = codeEl?.children ?? "";

            return (
              <pre
                {...props}
                className="relative overflow-x-auto rounded-lg border border-border/50 bg-[#0d1117] p-4 text-xs"
              >
                <CopyButton text={typeof codeText === "string" ? codeText : String(codeText)} />
                {children}
              </pre>
            );
          },
          // Prevent double-wrapping — let rehype-highlight handle code styling
          code({ className, children, ...props }) {
            const isBlock = className?.startsWith("language-");
            if (isBlock) {
              return (
                <code className={cn(className, "!bg-transparent !p-0")} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code
                className="rounded bg-muted px-1 py-0.5 text-xs text-velora-300"
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
