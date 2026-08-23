<div align="center">

# 🌙 Lunora

### *Pick a few films, name a feeling, and find ten more to watch tonight.*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Powered by TMDB](https://img.shields.io/badge/Powered%20by-TMDB-01B4E4?style=for-the-badge&logo=themoviedatabase&logoColor=white)](https://www.themoviedb.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-e8b84a?style=for-the-badge)](LICENSE)

<img src="https://img.shields.io/badge/status-active-6ba86e?style=flat-square" alt="status active">
<img src="https://img.shields.io/badge/frontend-vanilla%20JS-f0c565?style=flat-square" alt="vanilla js">
<img src="https://img.shields.io/badge/database-none%20needed-2a2f5e?style=flat-square" alt="no database">

</div>

<br>

> A mood-and-genre movie/TV recommender that queries **TMDB live** — no local database, no stale catalog. Pick up to five favorites, name a mood, filter by media type, or mix all three. Lunora scores everything on the fly using genre-vector cosine similarity, in a night-village pixel-art shell with full light/dark theming.

<br>

## 📖 Table of Contents

- [✨ Features](#-features)
- [🖼️ Preview](#️-preview)
- [🧠 How the Recommendation Engine Works](#-how-the-recommendation-engine-works)
- [🚀 Getting Started](#-getting-started)
- [🔌 API Reference](#-api-reference)
- [🎛️ Media Types & Moods](#️-media-types--moods)
- [🗂️ Project Structure](#️-project-structure)
- [⚠️ Known Limitations](#️-known-limitations)
- [📄 License](#-license)

<br>

## ✨ Features

| | |
|---|---|
| 🔎 **Live TMDB search** | Type-ahead seed picker searching TMDB's entire catalog — no local dataset to keep in sync |
| 🎟️ **Ticket-style picks** | Choose up to 5 favorite movies/shows as "seeds" for your recommendations |
| 🎭 **Mood filter** | 18 curated moods (*Cozy, Spooky, Mind-Bending, Epic...*), each a hand-tuned blend of genre weights |
| 🎬 **Genre filter** | Standard TMDB genre set, combinable with mood and media type |
| 📺 **Media type filter** | Narrow to Movie, TV Series, Anime, Animation, Documentary, Short Film, TV Movie, Reality TV, Talk Show, or Family & Kids |
| 🧩 **Zero-seed recommendations** | Genre, mood, or media type *alone* — no seed picks required — is enough to get results |
| 📡 **Where to watch** | Each result shows live streaming/rent/buy availability for your region |
| ♾️ **Infinite scroll** | Results paginate automatically as you scroll, powered by an offset-based API |
| 🌗 **Light & dark mode** | Full theme toggle with saved preference, defaulting to your OS setting on first visit |
| 🖼️ **Pixel-art hero** | Hand-built SVG night-village skyline with glowing windows and a chunky pixel-font title |

<br>

## 🖼️ Preview

<div align="center">
<i>Add screenshots here once you've got the app running — e.g.</i><br><br>

`docs/hero-dark.png` · `docs/hero-light.png` · `docs/recommendations.png`

</div>

<br>

## 🧠 How the Recommendation Engine Works

Lunora doesn't use a trained ML model — it uses **genre-vector cosine similarity**, which is simple, fast, explainable, and needs zero training data:

1. **Vectorize** — every title's genres become a normalized vector across TMDB's genre list (`vectorize.py`). TV-only genre labels (e.g. *"Sci-Fi & Fantasy"*) are mapped onto their movie-style equivalents so nothing gets silently dropped.
2. **Build the query vector** — from the average of your seed picks' genre vectors, or directly from your selected genre/mood filters if you picked no seeds at all.
3. **Pull a candidate pool** — live from TMDB's `/discover` endpoint, biased toward your genre and media-type filters, sorted by popularity.
4. **Score by cosine similarity** — each candidate is compared against your query vector. If a mood is selected, the score blends 60% seed/genre similarity with 40% mood-match similarity.
5. **Rank, paginate, enrich** — top matches are sorted, sliced by `offset`/`limit`, and enriched with live watch-provider data (streaming, free, rent, buy) fetched concurrently for just that page.

<br>

## 🚀 Getting Started

**Prerequisites:** Python 3.9+, and a free [TMDB API key](https://www.themoviedb.org/login).

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/lunora.git
cd lunora

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your TMDB API key
export TMDB_API_KEY="your_tmdb_key"

# 4. Start the backend
uvicorn api:app --reload
```

Then just open **`lunora.html`** in your browser — the frontend talks to the API at `http://127.0.0.1:8000` by default.

<br>

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/search?q=inception` | Live TMDB search, used to populate the seed picker |
| `GET` | `/genres` | List of genres for the filter UI |
| `GET` | `/moods` | List of mood presets for the filter UI |
| `GET` | `/media-types` | List of media type filters |
| `POST` | `/recommend` | Paginated recommendations, computed live from TMDB |

<details>
<summary><strong>Example <code>POST /recommend</code> request</strong></summary>

```json
{
  "movies": [
    { "tmdb_id": 27205, "title": "Inception", "genres": ["Action", "Science Fiction"] }
  ],
  "genres": ["Thriller"],
  "mood": "Mind-Bending",
  "media_type": null,
  "limit": 10,
  "offset": 0
}
```

Returns a `results` array (title, poster, genres, similarity score, content type, and where to watch) plus a `has_more` flag for infinite scroll.

</details>

<br>

## 🎛️ Media Types & Moods

<details>
<summary><strong>All 10 media types</strong></summary>
<br>

Movie · TV Series · Anime (animated + Japanese-language) · Animation (animated, non-anime) · Documentary · Short Film (≤40 min) · TV Movie · Reality TV · Talk Show · Family & Kids

</details>

<details>
<summary><strong>All 18 moods</strong></summary>
<br>

Cozy · Feel-Good · Slice of Life · Thrilling · Tense · Spooky · Dark & Gritty · Romantic · Heartwarming · Adventurous · Epic · Mind-Bending · Nostalgic · Chill · Wholesome · Historical · Whimsical · Intense Action

</details>

<br>

## 🗂️ Project Structure

```
lunora/
├── api.py              # FastAPI backend — search, discover, and /recommend
├── mood_config.py       # Genre list, mood taxonomy, media type taxonomy
├── vectorize.py         # Genre-vector math + mood matrix used by the API
├── lunora.html           # Frontend — single-file HTML/CSS/JS
├── requirements.txt      # Python dependencies
├── LICENSE                # MIT
└── README.md
```

<br>

## ⚠️ Known Limitations

- **No local database** — every search and recommendation hits TMDB live, so results depend on TMDB's uptime and rate limits.
- **Adult-content filtering** relies on TMDB's own `include_adult` flag, which catches literal adult-film content — not general content ratings like R or TV-MA.
- **"Short Film" is best-effort** — it filters on TMDB's runtime field, which has known accuracy gaps for some titles.
- **Watch-provider data** is fetched for `WATCH_REGION` (defaults to `US`) — change the constant in `api.py` for a different region.
- No automated tests yet — contributions welcome.

<br>

## 📄 License

Released under the [MIT License](LICENSE).

<br>

<div align="center">

*Built as a resume project — feedback and PRs welcome.*

</div>
