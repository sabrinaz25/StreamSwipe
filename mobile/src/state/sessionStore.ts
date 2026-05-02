import { create } from "zustand";

import { api } from "../api/client";
import type { FeedItem, Filters } from "../api/types";

type SessionState = {
  sessionId: string | null;
  filters: Filters;
  feed: FeedItem[];
  swiped: Record<string, "left" | "right">;
  isLoading: boolean;
  error: string | null;

  startSession: (filters: Filters) => Promise<void>;
  loadMore: () => Promise<void>;
  swipe: (itemId: string, direction: "left" | "right") => Promise<void>;
  reset: () => void;
};

const defaultFilters: Filters = { content_type: "movie", genre_ids: [], mood: null };

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: null,
  filters: defaultFilters,
  feed: [],
  swiped: {},
  isLoading: false,
  error: null,

  reset: () =>
    set({
      sessionId: null,
      filters: defaultFilters,
      feed: [],
      swiped: {},
      isLoading: false,
      error: null,
    }),

  startSession: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const { session_id } = await api.createSession({ filters });
      set({ sessionId: session_id, filters, feed: [], swiped: {} });
      const feed = await api.getFeed(session_id);
      set({ feed: feed.items, isLoading: false });
    } catch (e) {
      set({ isLoading: false, error: e instanceof Error ? e.message : "Unknown error" });
    }
  },

  loadMore: async () => {
    const { sessionId, isLoading } = get();
    if (!sessionId || isLoading) return;
    set({ isLoading: true, error: null });
    try {
      const feed = await api.getFeed(sessionId);
      set((s) => ({ feed: [...s.feed, ...feed.items], isLoading: false }));
    } catch (e) {
      set({ isLoading: false, error: e instanceof Error ? e.message : "Unknown error" });
    }
  },

  swipe: async (itemId, direction) => {
    const { sessionId } = get();
    if (!sessionId) return;
    set({ error: null });
    set((s) => ({
      swiped: { ...s.swiped, [itemId]: direction },
      feed: s.feed.filter((i) => i.item_id !== itemId),
    }));
    try {
      await api.swipe({ session_id: sessionId, item_id: itemId, direction });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Unknown error" });
    }
  },
}));

