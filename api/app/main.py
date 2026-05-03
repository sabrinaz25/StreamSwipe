from __future__ import annotations

import os
import secrets
import random
from typing import Sequence

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.integrations.tmdb import TMDBClient
from app.models import (
    ContentType,
    FeedItem,
    FeedResponse,
    RecommendationResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SwipeRequest,
    SwipeResponse,
)
from app.services.catalog import filter_items, load_demo_catalog
from app.services.collaborative import cf_dot_scores_for_session, refit_cf_if_needed
from app.services.recommend import build_justification, pick_best
from app.services.vectorize import update_profile_mean, vectorize_item
from app.storage.memory import MemoryStore, SessionState


load_dotenv()

APP_DEMO_MODE = os.getenv("APP_DEMO_MODE", "true").lower() == "true"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")

ALLOW_CORS_ORIGINS: Sequence[str] = tuple(
    o.strip() for o in os.getenv("APP_ALLOW_CORS_ORIGINS", "http://localhost:19006").split(",") if o.strip()
)

store = MemoryStore()
tmdb = TMDBClient(api_key=TMDB_API_KEY, base_url=TMDB_BASE_URL)

app = FastAPI(title="StreamSwipe API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOW_CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _seed_demo_catalog() -> None:
    for item in load_demo_catalog():
        store.upsert_item(item, vectorize_item(item))


@app.on_event("startup")
async def _startup() -> None:
    if APP_DEMO_MODE:
        _seed_demo_catalog()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/session", response_model=SessionCreateResponse)
async def create_session(req: SessionCreateRequest) -> SessionCreateResponse:
    session_id = secrets.token_urlsafe(16)
    random_start = random.randint(1, 5)
    store.sessions[session_id] = SessionState(
        session_id=session_id,
        created_at_ms=store.now_ms(),
        filters=req.filters,
        tmdb_pages={ct.value: random_start for ct in (req.filters.content_types or [])},
    )
    return SessionCreateResponse(session_id=session_id)


@app.get("/feed", response_model=FeedResponse)
async def get_feed(session_id: str, batch_size: int = 20) -> FeedResponse:
    s = store.sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    content_types = s.filters.content_types or []
    items: list[FeedItem] = []

    for ct in content_types:
        key = ct.value
        current_page = s.tmdb_pages.get(key, 1)

        if key == "anime":
            try:
                result = await tmdb.discover(content_type=ContentType.tv, genre_ids=[16], page=current_page, extra_params={"with_origin_country": "JP", "without_genres": "10749", "vote_count.gte": 100, "certification_country": "US", "certification.lte": "TV-14"})
                for it in result:
                    it = it.model_copy(update={"content_type": ContentType.anime})
                    if store.get_item_vec(it.item_id) is None:
                        store.upsert_item(it, vectorize_item(it))
                items.extend(result)
                s.tmdb_pages["anime"] = current_page + 1
            except Exception as e:
                continue

        if key not in ("movie", "tv"):
            continue
        try:
            result = await tmdb.discover(content_type=ct, genre_ids=s.filters.genre_ids, page=current_page, extra_params={"vote_count.gte": 100})
            items.extend(result)
            s.tmdb_pages[key] = current_page + 1
        except Exception as e:
            continue

    # Store all new items we got from TMDB
    for it in items:
        if store.get_item_vec(it.item_id) is None:
            store.upsert_item(it, vectorize_item(it))

    # Fall back to demo catalog only if TMDB returned nothing
    if not items:
        items = filter_items(
            list(store.items.values()),
            content_types=content_types,
            genre_ids=s.filters.genre_ids,
        )

    # Return items the session hasn't seen yet
    unseen = [it for it in items if it.item_id not in s.seen_item_ids]
    random.shuffle(unseen)
    return FeedResponse(session_id=session_id, items=unseen[:max(1, min(batch_size, 25))])


@app.post("/swipe", response_model=SwipeResponse)
async def post_swipe(req: SwipeRequest) -> SwipeResponse:
    s = store.sessions.get(req.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    item = store.get_item(req.item_id)
    vec = store.get_item_vec(req.item_id)
    if not item or vec is None:
        raise HTTPException(status_code=404, detail="item not found")

    if req.item_id not in s.seen_item_ids:
        s.seen_item_ids.add(req.item_id)
        if req.direction == "right":
            times_liked = s.like_counts.get(req.item_id, 0)
            weight = 2.0 if times_liked > 0 else 1.0
            s.like_counts[req.item_id] = times_liked + 1
            s.right_item_ids.append(req.item_id)
            s.profile_vec = update_profile_mean(s.profile_vec, vec, n_seen=len(s.right_item_ids), weight=weight)
            store.cf_dirty = True
        else:
            s.left_item_ids.append(req.item_id)

    return SwipeResponse(
        session_id=req.session_id,
        seen_count=len(s.seen_item_ids),
        right_count=len(s.right_item_ids),
        left_count=len(s.left_item_ids),
    )


@app.get("/recommendation", response_model=RecommendationResponse)
async def get_recommendation(session_id: str) -> RecommendationResponse:
    s = store.sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    effective_types = list(s.filters.content_types or [])
    if ContentType.anime in effective_types and ContentType.tv not in effective_types:
        effective_types.append(ContentType.tv)

    all_items = filter_items(
        list(store.items.values()),
        content_types=effective_types,
        genre_ids=s.filters.genre_ids,
    )
    candidates = [i for i in all_items if i.item_id not in s.seen_item_ids and i.item_id not in s.recommended_item_ids]

    refit_cf_if_needed(store)
    cand_ids = {i.item_id for i in candidates}
    cf_scores = cf_dot_scores_for_session(store, session_id, cand_ids)

    picked = pick_best(
        profile_vec=s.profile_vec,
        candidate_items=candidates,
        candidate_vecs=store.item_vecs,
        cf_scores=cf_scores or None,
    )
    if not picked:
        raise HTTPException(status_code=400, detail="not enough items to recommend")
    s.recommended_item_ids.add(picked.item.item_id)

    liked_items = [store.items[iid] for iid in s.right_item_ids if iid in store.items]
    justification = build_justification(
        picked=picked.item,
        liked=liked_items,
        candidate_vecs=store.item_vecs,
        profile_vec=s.profile_vec,
    )

    return RecommendationResponse(
        session_id=session_id,
        recommendation=picked.item,
        score=picked.score,
        justification=justification,
        where_to_watch=[],
    )

