"""
Loads FMA metadata (tracks.csv, features.csv), extracts a curated 13-dim
audio feature vector per track, builds album-order pseudo listening
sequences, normalizes, and writes train/val/test splits to disk.

Run `unzip fma_metadata.zip -d data/` first (see README.md).
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path("data/fma_metadata")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEQ_LEN = 5          # songs of context per sequence
SUBSET = "small"      # 'small' = 8,000 tracks / 8 balanced genres


def load_tracks() -> pd.DataFrame:
    tracks = pd.read_csv(DATA_DIR / "tracks.csv", index_col=0, header=[0, 1])
    tracks = tracks[tracks[("set", "subset")] == SUBSET]
    out = pd.DataFrame(index=tracks.index)
    out["album_id"] = tracks[("album", "id")]
    out["track_number"] = tracks[("track", "number")]
    out["genre"] = tracks[("track", "genre_top")]
    return out.dropna(subset=["album_id", "track_number", "genre"])
