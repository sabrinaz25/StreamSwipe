from __future__ import annotations

import hashlib

import numpy as np

from app.models import FeedItem


def _stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def vectorize_item(item: FeedItem, *, dim: int = 256) -> np.ndarray:
    v = np.zeros(dim + 1, dtype=np.float32)

    if 16 in item.genre_ids:
        if 28 in item.genre_ids or 10759 in item.genre_ids:
            idx = _stable_hash("anime:action") % dim
            v[idx] += 1.5
        if 9648 in item.genre_ids:
            idx = _stable_hash("anime:mystery") % dim
            v[idx] += 1.5
        if 10749 in item.genre_ids:
            idx = _stable_hash("anime:romance") % dim
            v[idx] += 1.5
        if 878 in item.genre_ids or 10765 in item.genre_ids:
            idx = _stable_hash("anime:scifi") % dim
            v[idx] += 1.5
        if 18 in item.genre_ids:
            idx = _stable_hash("anime:drama") % dim
            v[idx] += 1.5
            
    for g in item.genres:
        idx = _stable_hash(f"genre:{g.lower()}") % dim
        v[idx] += 1.0

    for gid in item.genre_ids:
        idx = _stable_hash(f"genre_id:{gid}") % dim
        v[idx] += 1.0

    for kw in item.keywords:
        idx = _stable_hash(f"kw:{kw.lower()}") % dim
        v[idx] += 1.0

    v[dim] = float(item.rating or 0.0) / 10.0
    n = np.linalg.norm(v)
    return v if n == 0 else (v / n)


def update_profile_mean(current: np.ndarray | None, new_vec: np.ndarray, *, n_seen: int, weight: float = 1.0) -> np.ndarray:
    if current is None or n_seen <= 1:
        merged = new_vec.copy()
    else:
        merged = (current * float(n_seen - 1) + new_vec * weight) / float(n_seen)

    n = np.linalg.norm(merged)
    return merged if n == 0 else (merged / n)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

