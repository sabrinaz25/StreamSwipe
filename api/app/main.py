from __future__ import annotations

import os
import secrets
from typing import Sequence

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.integrations.tmdb import TMDBClient
from app.models import (
    FeedResponse,
    RecommendationResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SwipeRequest,
    SwipeResponse,
)
from app.services.catalog import filter_items, load_demo_catalog
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
    store.sessions[session_id] = SessionState(
        session_id=session_id,
        created_at_ms=store.now_ms(),
        filters=req.filters,
    )
    return SessionCreateResponse(session_id=session_id)


@app.get("/feed", response_model=FeedResponse)
async def get_feed(session_id: str, batch_size: int = 15) -> FeedResponse:
    s = store.sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    items = []
    if s.filters.content_type.value in ("movie", "tv"):
        try:
            items = await tmdb.discover(
                content_type=s.filters.content_type,
                genre_ids=s.filters.genre_ids,
                page=1,
            )
        except Exception:
            items = []

    if not items:
        demo_items = filter_items(
            list(store.items.values()),
            content_type=s.filters.content_type,
            genre_ids=s.filters.genre_ids,
        )
        items = demo_items

    for it in items:
        if store.get_item_vec(it.item_id) is None:
            store.upsert_item(it, vectorize_item(it))

    unseen = [it for it in items if it.item_id not in s.seen_item_ids]
    return FeedResponse(session_id=session_id, items=unseen[: max(1, min(batch_size, 25))])


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
            s.right_item_ids.append(req.item_id)
            s.profile_vec = update_profile_mean(s.profile_vec, vec, n_seen=len(s.right_item_ids))
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

    all_items = filter_items(
        list(store.items.values()),
        content_type=s.filters.content_type,
        genre_ids=s.filters.genre_ids,
    )
    candidates = [i for i in all_items if i.item_id not in s.seen_item_ids]

    picked = pick_best(profile_vec=s.profile_vec, candidate_items=candidates, candidate_vecs=store.item_vecs)
    if not picked:
        raise HTTPException(status_code=400, detail="not enough items to recommend")

    liked_items = [store.items[iid] for iid in s.right_item_ids if iid in store.items]
    justification = build_justification(picked=picked.item, liked=liked_items)

    return RecommendationResponse(
        session_id=session_id,
        recommendation=picked.item,
        score=picked.score,
        justification=justification,
        where_to_watch=[],
    )

