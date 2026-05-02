from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    movie = "movie"
    tv = "tv"
    anime = "anime"


SwipeDirection = Literal["left", "right"]


class Filters(BaseModel):
    content_types: list[ContentType] = Field(default_factory=lambda: [ContentType.movie])
    genre_ids: list[int] = Field(default_factory=list)
    mood: str | None = Field(default=None, max_length=64)


class SessionCreateRequest(BaseModel):
    filters: Filters


class SessionCreateResponse(BaseModel):
    session_id: str


class FeedItem(BaseModel):
    item_id: str
    content_type: ContentType
    title: str
    overview: str
    poster_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    genre_ids: list[int] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    rating: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedResponse(BaseModel):
    session_id: str
    items: list[FeedItem]


class SwipeRequest(BaseModel):
    session_id: str
    item_id: str
    direction: SwipeDirection


class SwipeResponse(BaseModel):
    session_id: str
    seen_count: int
    right_count: int
    left_count: int


class RecommendationJustification(BaseModel):
    reason: str
    matched_genres: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    liked_titles: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    session_id: str
    recommendation: FeedItem
    score: float
    justification: RecommendationJustification
    where_to_watch: list[str] = Field(default_factory=list)

