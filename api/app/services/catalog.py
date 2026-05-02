from __future__ import annotations

import json
from pathlib import Path

from app.models import ContentType, FeedItem


def load_demo_catalog() -> list[FeedItem]:
    p = Path(__file__).resolve().parents[1] / "data" / "demo_catalog.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [FeedItem(**r) for r in raw]


def filter_items(items: list[FeedItem], *, content_types: list[ContentType], genre_ids: list[int]) -> list[FeedItem]:
    allowed = set(content_types)
    out = [i for i in items if i.content_type in allowed]
    if genre_ids:
        genre_set = set(genre_ids)
        out = [i for i in out if genre_set.intersection(i.genre_ids)]
    return out

