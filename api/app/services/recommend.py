from __future__ import annotations

from dataclasses import dataclass
import random

import numpy as np

from app.models import FeedItem, RecommendationJustification
from app.services.vectorize import cosine_similarity


@dataclass(frozen=True, slots=True)
class ScoredItem:
    item: FeedItem
    score: float


def pick_best(
    *,
    profile_vec: np.ndarray | None,
    candidate_items: list[FeedItem],
    candidate_vecs: dict[str, np.ndarray],
) -> ScoredItem | None:
    if profile_vec is None:
        if not candidate_items:
            return None
        best = max(candidate_items, key=lambda i: float(i.rating or 0.0))
        return ScoredItem(item=best, score=0.0)

    best_item: FeedItem | None = None
    best_score = -1.0
    for item in candidate_items:
        v = candidate_vecs.get(item.item_id)
        if v is None:
            continue
        s = cosine_similarity(profile_vec, v)
        if s > best_score:
            best_score = s
            best_item = item

    return None if best_item is None else ScoredItem(item=best_item, score=float(best_score))


def build_justification(
    *,
    picked: FeedItem,
    liked: list[FeedItem],
    candidate_vecs: dict[str, np.ndarray],
    profile_vec: np.ndarray | None,
) -> RecommendationJustification:
    
    picked_vec = candidate_vecs.get(picked.item_id)
    if picked_vec is not None and liked:
        scored = []
        for item in liked:
            v = candidate_vecs.get(item.item_id)
            if v is not None:
                scored.append((item, cosine_similarity(picked_vec, v)))
        scored.sort(key=lambda x: x[1], reverse=True)
        top_liked = [item for item, _ in scored[:3]]
    else:
        top_liked = liked[:3]

    liked_titles = [i.title for i in top_liked]
    liked_genres = set(g for i in liked for g in i.genres)
    liked_keywords = set(k for i in liked for k in i.keywords)

    matched_genres = [g for g in picked.genres if g in liked_genres][:3]
    matched_keywords = [k for k in picked.keywords if k in liked_keywords][:5]

    intros = [
        f"Because you enjoyed {', '.join(liked_titles)}",
        f"Based on your love of {', '.join(liked_titles)}",
        f"Fans of {', '.join(liked_titles)} tend to enjoy this",
        f"This pairs well with {', '.join(liked_titles)}",
    ] if liked_titles else ["Recommended based on your taste profile"]

    reason = random.choice(intros) + "."

    if matched_genres:
        reason += f" Shared genres: {', '.join(matched_genres)}."
    if matched_keywords:
        reason += f" Shared themes: {', '.join(matched_keywords)}."

    return RecommendationJustification(
        reason=reason,
        matched_genres=matched_genres,
        matched_keywords=matched_keywords,
        liked_titles=liked_titles,
    )
