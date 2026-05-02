from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from app.models import ContentType, FeedItem, Filters


@dataclass(slots=True)
class SessionState:
    session_id: str
    created_at_ms: int
    filters: Filters
    seen_item_ids: set[str] = field(default_factory=set)
    right_item_ids: list[str] = field(default_factory=list)
    left_item_ids: list[str] = field(default_factory=list)
    profile_vec: np.ndarray | None = None
    tmdb_pages: dict[str, int] = field(default_factory=dict)
    like_counts: dict[str, int] = field(default_factory=dict)


class MemoryStore:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionState] = {}
        self.items: dict[str, FeedItem] = {}
        self.item_vecs: dict[str, np.ndarray] = {}

    @staticmethod
    def now_ms() -> int:
        return int(time.time() * 1000)

    def upsert_item(self, item: FeedItem, vec: np.ndarray) -> None:
        self.items[item.item_id] = item
        self.item_vecs[item.item_id] = vec

    def get_item(self, item_id: str) -> FeedItem | None:
        return self.items.get(item_id)

    def get_item_vec(self, item_id: str) -> np.ndarray | None:
        return self.item_vecs.get(item_id)

    def list_items_by_type(self, content_type: ContentType) -> list[FeedItem]:
        return [i for i in self.items.values() if i.content_type == content_type]

