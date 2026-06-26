import { create } from "zustand";
import type { ConversationMessage, RoutingDecision } from "@/types";

function newConversationId(): string {
  return crypto.randomUUID();
}

const PREF_KEY = "velora_playground_prefs_v3";

type Strategy = "auto" | "cheapest" | "fastest" | "quality" | "manual";

function loadPrefs(): { strategy: Strategy; manualProvider: string; model: string } {
  if (typeof window === "undefined")
    return { strategy: "auto", manualProvider: "openai", model: "" };
  try {
    const raw = localStorage.getItem(PREF_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return { strategy: "auto", manualProvider: "openai", model: "" };
}

function savePrefs(strategy: Strategy, manualProvider: string, model: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(PREF_KEY, JSON.stringify({ strategy, manualProvider, model }));
}

interface PlaygroundState {
  messages: ConversationMessage[];
  isStreaming: boolean;
  selectedStrategy: Strategy;
  manualProvider: string;
  selectedModel: string;
  lastRoutingDecision: RoutingDecision | null;
  conversationId: string;

  addMessage: (msg: ConversationMessage) => void;
  updateLastAssistantMessage: (
    content: string,
    done?: boolean,
    routingDecision?: RoutingDecision
  ) => void;
  setError: (error: string) => void;
  setStreaming: (v: boolean) => void;
  setStrategy: (strategy: Strategy) => void;
  setManualProvider: (provider: string) => void;
  setModel: (model: string) => void;
  setLastRoutingDecision: (decision: RoutingDecision | null) => void;
  clearConversation: () => void;
}

const prefs = loadPrefs();

export const usePlaygroundStore = create<PlaygroundState>((set, get) => ({
  messages: [],
  isStreaming: false,
  selectedStrategy: prefs.strategy,
  manualProvider: prefs.manualProvider,
  selectedModel: prefs.model,
  lastRoutingDecision: null,
  conversationId: newConversationId(),

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  updateLastAssistantMessage: (content, done = false, routingDecision) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = {
          ...last,
          content,
          isStreaming: !done,
          ...(routingDecision ? { routing_decision: routingDecision } : {}),
        };
      }
      return {
        messages: msgs,
        ...(routingDecision ? { lastRoutingDecision: routingDecision } : {}),
      };
    }),

  setError: (error) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, isStreaming: false, error };
      }
      return { messages: msgs, isStreaming: false };
    }),

  setStreaming: (v) => set({ isStreaming: v }),

  setStrategy: (strategy) => {
    const { manualProvider, selectedModel } = get();
    set({ selectedStrategy: strategy });
    savePrefs(strategy, manualProvider, selectedModel);
  },

  setManualProvider: (provider) => {
    const { selectedStrategy, selectedModel } = get();
    set({ manualProvider: provider, selectedModel: "" });
    savePrefs(selectedStrategy, provider, selectedModel);
  },

  setModel: (model) => {
    const { selectedStrategy, manualProvider } = get();
    set({ selectedModel: model });
    savePrefs(selectedStrategy, manualProvider, model);
  },

  setLastRoutingDecision: (decision) =>
    set({ lastRoutingDecision: decision }),

  clearConversation: () =>
    set({ messages: [], isStreaming: false, lastRoutingDecision: null, conversationId: newConversationId() }),
}));
