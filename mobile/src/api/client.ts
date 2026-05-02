import type {
  FeedResponse,
  RecommendationResponse,
  SessionCreateRequest,
  SessionCreateResponse,
  SwipeRequest,
  SwipeResponse,
} from "./types";

import Constants from "expo-constants";

function inferApiBaseUrl(): string {
  // 1) Explicit override (recommended for web / production / CI).
  const explicitRaw = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  const explicit = explicitRaw ? explicitRaw.replace(/\/+$/, "") : null;

  // 2) On-device dev: derive from the Expo dev server host (same machine running the API).
  // hostUri looks like: "192.168.1.50:8081" or "localhost:8081"
  const hostUri =
    (Constants.expoConfig as any)?.hostUri ??
    (Constants as any)?.expoConfig?.hostUri ??
    (Constants as any)?.manifest2?.extra?.expoClient?.hostUri ??
    (Constants as any)?.manifest?.debuggerHost;

  if (typeof hostUri === "string" && hostUri.length > 0) {
    const host = hostUri.split("/")[0]?.split(":")[0];
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      const inferred = `http://${host}:8000`;
      // If someone accidentally set localhost in `.env`, override it for on-device dev.
      if (explicit && (explicit.includes("://localhost") || explicit.includes("://127.0.0.1"))) {
        return inferred;
      }
      if (!explicit) return inferred;
    }
  }

  // 3) If explicit is set (and not a bad localhost-on-device case), use it.
  if (explicit) return explicit;

  // 4) Default for local web development.
  return "http://localhost:8000";
}

const API_BASE_URL = inferApiBaseUrl();

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

