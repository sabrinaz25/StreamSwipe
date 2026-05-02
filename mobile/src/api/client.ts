import type {
  FeedResponse,
  RecommendationResponse,
  SessionCreateRequest,
  SessionCreateResponse,
  SwipeRequest,
  SwipeResponse,
} from "./types";

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return (await res.json()) as T;
}

export const api = {
  createSession: (body: SessionCreateRequest) =>
    http<SessionCreateResponse>("/session", { method: "POST", body: JSON.stringify(body) }),
  getFeed: (sessionId: string, batchSize = 15) =>
    http<FeedResponse>(`/feed?session_id=${encodeURIComponent(sessionId)}&batch_size=${batchSize}`),
  swipe: (body: SwipeRequest) =>
    http<SwipeResponse>("/swipe", { method: "POST", body: JSON.stringify(body) }),
  getRecommendation: (sessionId: string) =>
    http<RecommendationResponse>(`/recommendation?session_id=${encodeURIComponent(sessionId)}`),
  health: () => http<{ status: string }>("/health"),
};

