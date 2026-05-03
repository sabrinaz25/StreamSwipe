from __future__ import annotations

from dataclasses import dataclass

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

    w = cf_blend_weight if use_cf else 0.0
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

        if combined > best_score:
            best_score = combined
            best_item = item

    if best_item is None:
        return None
    return ScoredItem(item=best_item, score=float(best_score))


def build_justification(*, picked: FeedItem, liked: list[FeedItem]) -> RecommendationJustification:
    liked_titles = [i.title for i in liked[:3]]
    liked_genres = set(g for i in liked for g in i.genres)
    liked_keywords = set(k for i in liked for k in i.keywords)

    matched_genres = [g for g in picked.genres if g in liked_genres][:3]
    matched_keywords = [k for k in picked.keywords if k in liked_keywords][:5]

    if liked_titles:
        reason = f"Recommended because you liked {', '.join(liked_titles)}."
    else:
        reason = "Recommended based on your filters."

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

