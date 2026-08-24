"""
Shared vector math: converts a list of genre names into a normalized genre
vector, and builds the mood matrix used to score how well a genre vector
matches each mood preset. Used by both enrich_and_vectorize.py (offline,
for titles already in the local database) and api.py (live, for seed movies
picked from TMDB search that may not be in the local database at all).
"""

import numpy as np

from mood_config import GENRES, MOODS

# TMDB's TV genre names differ from movie genre names for a few overlapping
# concepts (e.g. TV has one combined "Action & Adventure" instead of separate
# "Action" and "Adventure"). Map those onto our movie-style GENRES list so a
# TV show's genres still contribute to its vector instead of being silently
# dropped.
TV_GENRE_ALIASES = {
    "Action & Adventure": ["Action", "Adventure"],
    "Sci-Fi & Fantasy": ["Science Fiction", "Fantasy"],
    "War & Politics": ["War"],
    "Kids": ["Family"],
    "Soap": ["Drama"],
    "Talk": ["Documentary"],
    "News": ["Documentary"],
}


def normalize_genre_names(genre_names: list) -> list:
    """Expand any TV-style compound genre names into their movie-style equivalents."""
    normalized = []
    for g in genre_names:
        normalized.extend(TV_GENRE_ALIASES.get(g, [g]))
    return normalized


def genre_vector_for(genre_names: list) -> np.ndarray:
    genre_names = normalize_genre_names(genre_names)
    vec = np.zeros(len(GENRES))
    for g in genre_names:
        if g in GENRES:
            vec[GENRES.index(g)] = 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def mood_matrix() -> np.ndarray:
    """Rows = moods, columns = genres, in MOODS/GENRES order, each row normalized."""
    matrix = np.zeros((len(MOODS), len(GENRES)))
    for i, weights in enumerate(MOODS.values()):
        for genre, weight in weights.items():
            if genre in GENRES:
                matrix[i, GENRES.index(genre)] = weight
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms


def mood_scores_for(genre_vector: np.ndarray) -> dict:
    mood_names = list(MOODS.keys())
    mat = mood_matrix()
    return {
        mood_names[j]: round(float(mat[j] @ genre_vector), 4)
        for j in range(len(mood_names))
    }
