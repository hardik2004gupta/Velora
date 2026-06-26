import { create } from "zustand";
import type { ConversationMessage } from "@/types";

// Persisted provider/model preference (client-side only, replaced by server
// settings in a future phase).
const PREF_KEY = "velora_playground_prefs";

function loadPrefs(): { provider: string; model: string } {
  if (typeof window === "undefined") return { provider: "openai", model: "" };
  try {
    const raw = localStorage.getItem(PREF_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return { provider: "openai", model: "" };
}

function savePrefs(provider: string, model: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(PREF_KEY, JSON.stringify({ provider, model }));
}

interface PlaygroundState {
  messages: ConversationMessage[];
  isStreaming: boolean;
  selectedProvider: string;
  selectedModel: string;

  addMessage: (msg: ConversationMessage) => void;
  updateLastAssistantMessage: (content: string, done?: boolean) => void;
  setError: (error: string) => void;
  setStreaming: (v: boolean) => void;
  setProvider: (provider: string) => void;
  setModel: (model: string) => void;
  clearConversation: () => void;
}

const prefs = loadPrefs();

export const usePlaygroundStore = create<PlaygroundState>((set, get) => ({
  messages: [],
  isStreaming: false,
  selectedProvider: prefs.provider,
  selectedModel: prefs.model,

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  updateLastAssistantMessage: (content, done = false) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = {
          ...last,
          content,
          isStreaming: !done,
        };
      }
      return { messages: msgs };
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

  setProvider: (provider) => {
    set({ selectedProvider: provider, selectedModel: "" });
    savePrefs(provider, "");
  },

  setModel: (model) => {
    const { selectedProvider } = get();
    set({ selectedModel: model });
    savePrefs(selectedProvider, model);
  },

  clearConversation: () => set({ messages: [], isStreaming: false }),
}));
