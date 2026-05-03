from __future__ import annotations

from typing import Any

from fastapi import params

import httpx

from app.models import ContentType, FeedItem

TMDB_GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    # TV specific
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics", 
}

class TMDBClient:
    def __init__(self, *, api_key: str, base_url: str = "https://api.themoviedb.org/3") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def discover(self, *, content_type: ContentType, genre_ids: list[int], page: int = 1, extra_params: dict[str, Any] | None = None,) -> list[FeedItem]:
        if not self._api_key:
            return []

        all_items: list[FeedItem] = []
    
        for p in range(page, page + 3):
            endpoint = "discover/movie" if content_type == ContentType.movie else "discover/tv"
            params: dict[str, Any] = {
                "api_key": self._api_key,
                "page": p,
                "include_adult": "false",
                "with_genres": ",".join(str(g) for g in genre_ids) if genre_ids else None,
                "sort_by": "popularity.desc",
                "vote_count.gte": 100,
                "without_genres": "10749",
            }
            if extra_params:
                params.update(extra_params)
            params = {k: v for k, v in params.items() if v is not None}

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(f"{self._base_url}/{endpoint}", params=params)
                    r.raise_for_status()
                    data = r.json()

                for row in data.get("results", []):
                    title = row.get("title") or row.get("name") or "Untitled"
                    poster_path = row.get("poster_path")
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                    tmdb_id = row.get("id")
                    item_id = f"tmdb_{content_type.value}_{tmdb_id}"
                    genre_ids_list = row.get("genre_ids") or []
                    genres = [TMDB_GENRE_MAP[gid] for gid in genre_ids_list if gid in TMDB_GENRE_MAP]
                    all_items.append(
                        FeedItem(
                            item_id=item_id,
                            content_type=content_type,
                            title=title,
                            overview=row.get("overview") or "",
                            poster_url=poster_url,
                            genre_ids=genre_ids_list,
                            genres=genres,
                            keywords=[],
                            rating=float(row.get("vote_average") or 0.0),
                            metadata={"tmdb_id": tmdb_id},
                        )
                    )
            except Exception as e:
                continue

        return all_items
    
    async def trending(self, *, content_type: ContentType, page: int = 1) -> list[FeedItem]:
        if not self._api_key:
            return []
        media = "movie" if content_type == ContentType.movie else "tv"
        params = {"api_key": self._api_key, "page": page}
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{self._base_url}/trending/{media}/week", params=params)
            r.raise_for_status()
            data = r.json()

        items = []
        for row in data.get("results", []):
            title = row.get("title") or row.get("name") or "Untitled"
            poster_path = row.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            tmdb_id = row.get("id")
            genre_ids_list = row.get("genre_ids") or []
            genres = [TMDB_GENRE_MAP[gid] for gid in genre_ids_list if gid in TMDB_GENRE_MAP]
            items.append(
                FeedItem(
                    item_id=f"tmdb_{content_type.value}_{tmdb_id}",
                    content_type=content_type,
                    title=title,
                    overview=row.get("overview") or "",
                    poster_url=poster_url,
                    genre_ids=genre_ids_list,
                    genres=genres,
                    keywords=[],
                    rating=float(row.get("vote_average") or 0.0),
                    metadata={"tmdb_id": tmdb_id},
                )
            )
        return items
