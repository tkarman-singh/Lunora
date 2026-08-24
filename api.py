"""
FastAPI backend serving movie search, filters, and mood/genre-based
recommendations for the Lunora frontend.

Both search AND recommendations are powered live by TMDB -- no local
database needed at all. Recommendations work with seed movies, filters, or
both: pick up to 5 favorites, pick a genre/mood, or just use the filters
alone with no seeds at all. Results are paginated via `offset` so the
frontend can load more as the user scrolls, and each result is enriched
with where it's currently available to watch and what kind of title it is
(movie / TV series / anime).

Setup:
    export TMDB_API_KEY="your_tmdb_key"
    pip install -r requirements.txt
    uvicorn api:app --reload

Endpoints:
    GET  /search?q=inception   -> live TMDB search for the seed picker
    GET  /genres               -> list of genres for the filter UI
    GET  /moods                -> list of moods for the filter UI
    POST /recommend            -> paginated recommendations, live from TMDB
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import numpy as np
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mood_config import GENRES, MEDIA_TYPES, MOODS
from vectorize import genre_vector_for, mood_matrix, TV_GENRE_ALIASES

TMDB_BASE = "https://api.themoviedb.org/3"
WATCH_REGION = "US"  # change this if you want watch-provider data for a different country

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    sys.exit("Set TMDB_API_KEY as an environment variable before starting the API.")

app = FastAPI(title="Lunora API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your real frontend origin before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_session() -> requests.Session:
    """A requests session that automatically retries dropped connections
    and rate-limit responses instead of raising immediately."""
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = make_session()


# ---------- TMDB genre id <-> name maps, loaded once at startup ----------

def load_genre_map(kind: str) -> dict:
    resp = SESSION.get(f"{TMDB_BASE}/genre/{kind}/list", params={"api_key": TMDB_API_KEY}, timeout=15)
    resp.raise_for_status()
    return {g["id"]: g["name"] for g in resp.json().get("genres", [])}


MOVIE_GENRE_MAP = load_genre_map("movie")
TV_GENRE_MAP = load_genre_map("tv")
NAME_TO_MOVIE_ID = {v: k for k, v in MOVIE_GENRE_MAP.items()}
NAME_TO_TV_ID = {v: k for k, v in TV_GENRE_MAP.items()}

for tv_name, movie_names in TV_GENRE_ALIASES.items():
    tv_id = NAME_TO_TV_ID.get(tv_name)
    if tv_id is None:
        continue
    for mn in movie_names:
        NAME_TO_TV_ID.setdefault(mn, tv_id)


class SeedMovie(BaseModel):
    tmdb_id: int
    title: str
    genres: List[str]


class RecommendRequest(BaseModel):
    movies: List[SeedMovie] = []            # 0-5 seeds; can be empty if genres/mood given
    genres: Optional[List[str]] = None       # genre filter, e.g. ["Comedy", "Romance"]
    mood: Optional[str] = None               # mood filter, e.g. "Cozy"
    media_type: Optional[str] = None         # one of MEDIA_TYPES, e.g. "Anime"
    include_adult: bool = False              # NSFW toggle -- off by default
    limit: int = 10
    offset: int = 0                          # for infinite scroll / "load more"


@app.get("/search")
def search_titles(q: str = Query(..., min_length=1), include_adult: bool = Query(False)):
    """Live search across TMDB's full catalog -- any movie or show ever made."""
    try:
        resp = SESSION.get(
            f"{TMDB_BASE}/search/multi",
            params={"api_key": TMDB_API_KEY, "query": q, "include_adult": str(include_adult).lower()},
            timeout=15,
        )
    except requests.exceptions.RequestException:
        raise HTTPException(503, "Couldn't reach TMDB right now -- check your connection and try again.")

    if resp.status_code != 200:
        raise HTTPException(502, "TMDB search failed.")

    results = []
    for r in resp.json().get("results", []):
        media_type = r.get("media_type")
        if media_type not in ("movie", "tv"):
            continue

        genre_map = MOVIE_GENRE_MAP if media_type == "movie" else TV_GENRE_MAP
        genre_names = [genre_map[gid] for gid in r.get("genre_ids", []) if gid in genre_map]
        title = r.get("title") or r.get("name")
        date = r.get("release_date") or r.get("first_air_date") or ""

        results.append({
            "tmdb_id": r["id"],
            "media_type": media_type,
            "title": title,
            "year": date[:4] if date else None,
            "poster_path": r.get("poster_path"),
            "genres": genre_names,
            "popularity": r.get("popularity", 0),
        })

    results.sort(key=lambda r: r["popularity"], reverse=True)
    return results[:10]


@app.get("/genres")
def list_genres():
    return GENRES


@app.get("/moods")
def list_moods():
    return list(MOODS.keys())


@app.get("/media-types")
def list_media_types():
    return list(MEDIA_TYPES.keys())


def content_type_for(media_type: str, genre_names: list, original_language: str) -> str:
    if "Animation" in genre_names and original_language == "ja":
        return "Anime"
    return "TV Series" if media_type == "tv" else "Movie"


def fetch_discover_candidates(
    media_type: str, genre_ids: list, pages: int = 5,
    include_adult: bool = False, extra_params: Optional[dict] = None,
) -> list:
    """Pull a pool of candidates from TMDB Discover, sorted by popularity and
    deduped by id. If genre_ids is empty, falls back to plain popularity
    browsing. A page that fails even after retries is skipped rather than
    blowing up the whole request. pages=5 gives a big enough pool (~100 per
    media type) to support several rounds of 'load more'."""
    seen = {}
    for page in range(1, pages + 1):
        params = {
            "api_key": TMDB_API_KEY,
            "sort_by": "popularity.desc",
            "page": page,
            "include_adult": str(include_adult).lower(),
        }
        if genre_ids:
            params["with_genres"] = "|".join(str(g) for g in genre_ids)
        if extra_params:
            params.update(extra_params)

        try:
            resp = SESSION.get(f"{TMDB_BASE}/discover/{media_type}", params=params, timeout=15)
        except requests.exceptions.RequestException:
            break

        if resp.status_code != 200:
            break
        data = resp.json()
        for r in data.get("results", []):
            seen[r["id"]] = r
        if page >= data.get("total_pages", 1):
            break
    return list(seen.values())


def fetch_watch_providers(media_type: str, tmdb_id: int) -> dict:
    """Return where a title can currently be watched in WATCH_REGION.
    Prioritizes subscription streaming, then free, then rent/buy."""
    try:
        resp = SESSION.get(
            f"{TMDB_BASE}/{media_type}/{tmdb_id}/watch/providers",
            params={"api_key": TMDB_API_KEY},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        return {"type": None, "providers": [], "link": None}

    if resp.status_code != 200:
        return {"type": None, "providers": [], "link": None}

    region_data = resp.json().get("results", {}).get(WATCH_REGION)
    if not region_data:
        return {"type": None, "providers": [], "link": None}

    for kind, label in [
        ("flatrate", "Streaming"), ("free", "Free"), ("ads", "Free with ads"),
        ("rent", "Rent"), ("buy", "Buy"),
    ]:
        entries = region_data.get(kind)
        if entries:
            names = sorted({e["provider_name"] for e in entries})
            return {"type": label, "providers": names, "link": region_data.get("link")}

    return {"type": None, "providers": [], "link": region_data.get("link")}


@app.post("/recommend")
def recommend(req: RecommendRequest):
    if len(req.movies) > 5:
        raise HTTPException(400, "Provide at most 5 movies.")
    if not req.movies and not req.genres and not req.mood and not req.media_type:
        raise HTTPException(400, "Provide at least one movie, genre, mood, or media type to base recommendations on.")
    if req.media_type and req.media_type not in MEDIA_TYPES:
        raise HTTPException(400, f"Unknown media_type. Choose from: {list(MEDIA_TYPES.keys())}")

    type_spec = MEDIA_TYPES.get(req.media_type) if req.media_type else None
    media_types_to_fetch = type_spec["media_types"] if type_spec else ["movie", "tv"]

    # Build the query vector: from your seed movies if given, otherwise
    # straight from the genre/mood filters, so recommendations work even
    # with zero seeds selected.
    if req.movies:
        seed_vectors = np.array([genre_vector_for(m.genres) for m in req.movies])
        query_vector = seed_vectors.mean(axis=0)
    else:
        parts = []
        if req.mood and req.mood in MOODS:
            parts.append(mood_matrix()[list(MOODS.keys()).index(req.mood)])
        if req.genres:
            parts.append(genre_vector_for(req.genres))
        if not parts:
            # Nothing but a media_type was given (e.g. just "show me anime") --
            # no genre/mood direction to rank by, so use a flat vector; the
            # media_type filter below still does the real narrowing.
            parts.append(np.ones(len(GENRES)) / len(GENRES))
        query_vector = np.mean(parts, axis=0)

    qnorm = np.linalg.norm(query_vector)
    if qnorm > 0:
        query_vector = query_vector / qnorm

    # Candidate pool genres: explicit filter if given, otherwise the union
    # of the seed movies' own genres. A selected mood broadens the pool
    # further so it can actually shift results, not just re-rank them.
    if req.genres:
        filter_names = set(req.genres)
    else:
        filter_names = set()
        for m in req.movies:
            filter_names.update(m.genres)
    if req.mood and req.mood in MOODS:
        filter_names |= set(MOODS[req.mood].keys())
    if type_spec and type_spec.get("require_genre_any"):
        # Feed the type's required genre(s) into the discover query itself
        # (not just the post-filter below) so e.g. selecting "Anime" alone
        # actually surfaces anime candidates instead of filtering a mostly
        # unrelated popularity pool down to nothing.
        filter_names |= set(type_spec["require_genre_any"])

    movie_genre_ids = [NAME_TO_MOVIE_ID[g] for g in filter_names if g in NAME_TO_MOVIE_ID]
    tv_genre_ids = [NAME_TO_TV_ID[g] for g in filter_names if g in NAME_TO_TV_ID]

    candidates = []
    if "movie" in media_types_to_fetch:
        extra = {}
        if type_spec and type_spec.get("max_runtime"):
            extra["with_runtime.lte"] = type_spec["max_runtime"]
        if type_spec and type_spec.get("require_language"):
            extra["with_original_language"] = type_spec["require_language"]
        fetched = fetch_discover_candidates(
            "movie", movie_genre_ids, include_adult=req.include_adult, extra_params=extra
        )
        candidates.extend((r, "movie") for r in fetched)
    if "tv" in media_types_to_fetch:
        extra = {}
        if type_spec and type_spec.get("require_language"):
            extra["with_original_language"] = type_spec["require_language"]
        fetched = fetch_discover_candidates(
            "tv", tv_genre_ids, include_adult=req.include_adult, extra_params=extra
        )
        candidates.extend((r, "tv") for r in fetched)

    mood_row = None
    if req.mood and req.mood in MOODS:
        mood_row = mood_matrix()[list(MOODS.keys()).index(req.mood)]

    seed_ids = {m.tmdb_id for m in req.movies}
    scored = []
    for r, media_type in candidates:
        if r["id"] in seed_ids:
            continue

        genre_map = MOVIE_GENRE_MAP if media_type == "movie" else TV_GENRE_MAP
        genre_names = [genre_map[gid] for gid in r.get("genre_ids", []) if gid in genre_map]
        original_language = r.get("original_language", "")

        if type_spec:
            req_any = type_spec.get("require_genre_any")
            if req_any and not any(g in genre_names for g in req_any):
                continue
            if type_spec.get("require_language") and original_language != type_spec["require_language"]:
                continue
            if type_spec.get("exclude_language") and original_language == type_spec["exclude_language"]:
                continue

        vec = genre_vector_for(genre_names)
        sim = float(np.dot(query_vector, vec))

        if mood_row is not None:
            mood_score = float(np.dot(mood_row, vec))
            sim = 0.6 * sim + 0.4 * mood_score

        title = r.get("title") or r.get("name")
        date = r.get("release_date") or r.get("first_air_date") or ""
        scored.append((sim, {
            "tmdb_id": r["id"],
            "media_type": media_type,
            "content_type": content_type_for(media_type, genre_names, original_language),
            "title": title,
            "year": date[:4] if date else None,
            "poster_path": r.get("poster_path"),
            "genres": genre_names,
            "similarity": round(sim, 4),
        }))

    scored.sort(key=lambda x: x[0], reverse=True)

    page = scored[req.offset: req.offset + req.limit]
    has_more = (req.offset + req.limit) < len(scored)

    # Fetch "where to watch" concurrently for just this page -- not the
    # whole candidate pool -- so this stays fast regardless of pool size.
    def attach_providers(entry):
        _, item = entry
        item["where_to_watch"] = fetch_watch_providers(item["media_type"], item["tmdb_id"])
        return item

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attach_providers, page))

    return {"results": results, "has_more": has_more}
