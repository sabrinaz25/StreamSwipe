export type ContentType = "movie" | "tv" | "anime";
export type SwipeDirection = "left" | "right";

export type Filters = {
  content_type: ContentType;
  genre_ids: number[];
  mood?: string | null;
};

export type SessionCreateRequest = {
  filters: Filters;
};

export type SessionCreateResponse = {
  session_id: string;
};

export type FeedItem = {
  item_id: string;
  content_type: ContentType;
  title: string;
  overview: string;
  poster_url?: string | null;
  genres: string[];
  genre_ids: number[];
  keywords: string[];
  rating?: number | null;
  metadata: Record<string, unknown>;
};

export type FeedResponse = {
  session_id: string;
  items: FeedItem[];
};

export type SwipeRequest = {
  session_id: string;
  item_id: string;
  direction: SwipeDirection;
};

export type SwipeResponse = {
  session_id: string;
  seen_count: number;
  right_count: number;
  left_count: number;
};

export type RecommendationJustification = {
  reason: string;
  matched_genres: string[];
  matched_keywords: string[];
  liked_titles: string[];
};

export type RecommendationResponse = {
  session_id: string;
  recommendation: FeedItem;
  score: number;
  justification: RecommendationJustification;
  where_to_watch: string[];
};
