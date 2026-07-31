/**
 * Chat store — global state for the chatbot conversation.
 *
 * Uses Zustand for minimal boilerplate. Stores messages,
 * loading state, and provides actions to send messages
 * through the backend API.
 */

import { create } from "zustand";
import { sendChatMessage, type ChatResponse } from "@/services/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoning?: string[];
  sources?: { name: string; snippet: string; type: string; score: number }[];
  is_safe?: boolean;
  timestamp: Date;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (query: string) => Promise<void>;
  clearMessages: () => void;
}

/**
 * Generate a unique ID for each message.
 * Uses crypto.randomUUID where available, falls back to timestamp.
 */
function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,

  sendMessage: async (query: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    // Add user message and set loading
    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response: ChatResponse = await sendChatMessage(query);

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: response.answer,
        reasoning: response.reasoning,
        sources: response.sources,
        is_safe: response.is_safe,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "An unexpected error occurred";

      set((state) => ({
        messages: [
          ...state.messages,
          {
            id: generateId(),
            role: "assistant" as const,
            content: `⚠️ Error: ${errorMessage}. Make sure the Python backend is running on port 8000.`,
            timestamp: new Date(),
          },
        ],
        isLoading: false,
        error: errorMessage,
      }));
    }
  },

  clearMessages: () => set({ messages: [], error: null }),
}));
