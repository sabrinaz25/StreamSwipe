from __future__ import annotations

from typing import Any

import httpx

from app.models import ContentType, FeedItem


class TMDBClient:
    def __init__(self, *, api_key: str, base_url: str = "https://api.themoviedb.org/3") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def discover(self, *, content_type: ContentType, genre_ids: list[int], page: int = 1) -> list[FeedItem]:
        if not self._api_key:
            return []

        endpoint = "discover/movie" if content_type == ContentType.movie else "discover/tv"
        params: dict[str, Any] = {
            "api_key": self._api_key,
            "page": page,
            "include_adult": "false",
            "with_genres": ",".join(str(g) for g in genre_ids) if genre_ids else None,
            "sort_by": "popularity.desc",
        }
        params = {k: v for k, v in params.items() if v is not None}

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{self._base_url}/{endpoint}", params=params)
            r.raise_for_status()
            data = r.json()

        items: list[FeedItem] = []
        for row in data.get("results", []):
            title = row.get("title") or row.get("name") or "Untitled"
            poster_path = row.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            tmdb_id = row.get("id")
            item_id = f"tmdb_{content_type.value}_{tmdb_id}"
            items.append(
                FeedItem(
                    item_id=item_id,
                    content_type=content_type,
                    title=title,
                    overview=row.get("overview") or "",
                    poster_url=poster_url,
                    genre_ids=row.get("genre_ids") or [],
                    genres=[],
                    keywords=[],
                    rating=float(row.get("vote_average") or 0.0),
                    metadata={"tmdb_id": tmdb_id},
                )
            )

        return items

