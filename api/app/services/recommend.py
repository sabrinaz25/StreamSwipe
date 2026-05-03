from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import random

import numpy as np

from app.models import FeedItem, RecommendationJustification
from app.services.vectorize import cosine_similarity


@dataclass(frozen=True, slots=True)
class ScoredItem:
    item: FeedItem
    score: float


def _minmax_scores(raw: dict[str, float]) -> dict[str, float]:
    if not raw:
        return {}
    vals = list(raw.values())
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return {k: 0.5 for k in raw}
    return {k: (v - lo) / (hi - lo) for k, v in raw.items()}


def _content_scores(
    *,
    profile_vec: np.ndarray | None,
    candidate_items: list[FeedItem],
    candidate_vecs: dict[str, np.ndarray],
) -> dict[str, float]:
    out: dict[str, float] = {}
    if profile_vec is not None:
        for item in candidate_items:
            v = candidate_vecs.get(item.item_id)
            out[item.item_id] = cosine_similarity(profile_vec, v) if v is not None else 0.0
    else:
        for item in candidate_items:
            out[item.item_id] = float(item.rating or 0.0) / 10.0
    return out


def _dislike_similarity_raw(
    *,
    candidate_items: list[FeedItem],
    candidate_vecs: dict[str, np.ndarray],
    disliked_item_ids: Sequence[str],
) -> dict[str, float]:
    """Max cosine(candidate, disliked) per candidate; high means close to something the user disliked."""
    d_vecs = [
        candidate_vecs[i]
        for i in dict.fromkeys(disliked_item_ids)
        if i in candidate_vecs
    ]
    if not d_vecs:
        return {it.item_id: 0.0 for it in candidate_items}

    out: dict[str, float] = {}
    for item in candidate_items:
        v = candidate_vecs.get(item.item_id)
        if v is None:
            out[item.item_id] = 0.0
            continue
        out[item.item_id] = max(cosine_similarity(v, dv) for dv in d_vecs)
    return out


def _normalize_dislike_penalty(dislike_raw: dict[str, float]) -> dict[str, float]:
    if not dislike_raw:
        return {}
    vals = list(dislike_raw.values())
    if max(vals) < 1e-9:
        return {k: 0.0 for k in dislike_raw}
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return {k: 1.0 for k in dislike_raw}
    return {k: (v - lo) / (hi - lo) for k, v in dislike_raw.items()}


def _cf_signal_strength(cf_raw: dict[str, float]) -> bool:
    if not cf_raw:
        return False
    vals = list(cf_raw.values())
    return (max(vals) - min(vals) > 1e-9) or (max(vals) > 1e-6)


def pick_best(
    *,
    profile_vec: np.ndarray | None,
    candidate_items: list[FeedItem],
    candidate_vecs: dict[str, np.ndarray],
    cf_scores: dict[str, float] | None = None,
    cf_blend_weight: float = 0.38,
    disliked_item_ids: Sequence[str] | None = None,
    dislike_penalty_weight: float = 0.35,
) -> ScoredItem | None:
    if not candidate_items:
        return None

    content_raw = _content_scores(
        profile_vec=profile_vec, candidate_items=candidate_items, candidate_vecs=candidate_vecs
    )
    content_n = _minmax_scores(content_raw)

    cf_raw = {it.item_id: float(cf_scores.get(it.item_id, 0.0)) for it in candidate_items} if cf_scores else {}
    use_cf = cf_scores is not None and _cf_signal_strength(cf_raw)
    cf_n = _minmax_scores(cf_raw) if use_cf else {}

    dislikes = list(disliked_item_ids) if disliked_item_ids else []
    dislike_raw = (
        _dislike_similarity_raw(
            candidate_items=candidate_items,
            candidate_vecs=candidate_vecs,
            disliked_item_ids=dislikes,
        )
        if dislikes
        else {it.item_id: 0.0 for it in candidate_items}
    )
    dislike_n = _normalize_dislike_penalty(dislike_raw) if dislikes else {it.item_id: 0.0 for it in candidate_items}

    w = cf_blend_weight if use_cf else 0.0
    w_d = max(0.0, min(1.0, float(dislike_penalty_weight)))
    best_item: FeedItem | None = None
    best_score = -1.0
    for item in candidate_items:
        cid = item.item_id
        c_part = content_n.get(cid, 0.0)
        if use_cf:
            f_part = cf_n.get(cid, 0.0)
            combined = (1.0 - w) * c_part + w * f_part
        else:
            combined = c_part
        if profile_vec is None and not use_cf:
            combined = content_raw.get(cid, 0.0)

        d_part = dislike_n.get(cid, 0.0)
        adjusted = combined * (1.0 - w_d * d_part)

        if adjusted > best_score:
            best_score = adjusted
            best_item = item

    if best_item is None:
        return None
    return ScoredItem(item=best_item, score=float(best_score))


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
