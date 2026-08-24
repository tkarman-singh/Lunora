"""
Mood taxonomy: each mood is a set of weighted genre affinities.
Add a new mood by adding one entry here — nothing else needs to change,
the vectorizer and API pick it up automatically.

Genre names must match TMDB's genre names exactly.
"""

GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western",
]

MOODS = {
    "Cozy": {"Comedy": 1.0, "Family": 0.8, "Romance": 0.3},
    "Feel-Good": {"Comedy": 1.0, "Family": 0.6, "Music": 0.3},
    "Slice of Life": {"Drama": 0.6, "Romance": 0.6, "Comedy": 0.6},
    "Thrilling": {"Action": 1.0, "Thriller": 1.0, "Crime": 0.3},
    "Tense": {"Thriller": 1.0, "Mystery": 0.6, "Crime": 0.5},
    "Spooky": {"Horror": 1.0, "Mystery": 0.5, "Thriller": 0.3},
    "Dark & Gritty": {"Crime": 1.0, "Thriller": 0.8, "Drama": 0.5},
    "Romantic": {"Romance": 1.0, "Drama": 0.4, "Comedy": 0.3},
    "Heartwarming": {"Family": 1.0, "Drama": 0.5, "Romance": 0.4},
    "Adventurous": {"Adventure": 1.0, "Action": 0.6, "Fantasy": 0.5},
    "Epic": {"Action": 0.8, "Adventure": 0.8, "Fantasy": 0.6, "War": 0.5},
    "Mind-Bending": {"Science Fiction": 1.0, "Mystery": 0.7, "Thriller": 0.5},
    "Nostalgic": {"Drama": 0.5, "Family": 0.4, "Music": 0.4},
    "Chill": {"Documentary": 0.5, "Drama": 0.4, "Comedy": 0.4},
    "Wholesome": {"Family": 1.0, "Animation": 0.6, "Comedy": 0.4},
    "Historical": {"History": 1.0, "War": 0.5, "Drama": 0.4},
    "Whimsical": {"Fantasy": 1.0, "Animation": 0.6, "Family": 0.4},
    "Intense Action": {"Action": 1.0, "War": 0.4, "Crime": 0.3},
}

# Media type taxonomy: each type narrows which TMDB endpoints get queried
# and/or which genre or language a candidate must match. Add a new type by
# adding one entry here.
#   media_types        -- which TMDB endpoints to query ("movie", "tv", or both)
#   require_genre_any  -- candidate must have at least one of these genres
#   require_language   -- candidate's original_language must equal this
#   exclude_language    -- candidate's original_language must NOT equal this
#   max_runtime        -- movie runtime cap in minutes (TMDB discover-side filter;
#                          TMDB's own runtime data has known accuracy gaps, so
#                          this is best-effort, not exact)
MEDIA_TYPES = {
    "Movie": {"media_types": ["movie"]},
    "TV Series": {"media_types": ["tv"]},
    "Anime": {"media_types": ["movie", "tv"], "require_genre_any": ["Animation"], "require_language": "ja"},
    "Animation": {"media_types": ["movie", "tv"], "require_genre_any": ["Animation"], "exclude_language": "ja"},
    "Documentary": {"media_types": ["movie", "tv"], "require_genre_any": ["Documentary"]},
    "Short Film": {"media_types": ["movie"], "max_runtime": 40},
    "TV Movie": {"media_types": ["movie"], "require_genre_any": ["TV Movie"]},
    "Reality TV": {"media_types": ["tv"], "require_genre_any": ["Reality"]},
    "Talk Show": {"media_types": ["tv"], "require_genre_any": ["Talk"]},
    "Family & Kids": {"media_types": ["movie", "tv"], "require_genre_any": ["Family", "Kids"]},
}
