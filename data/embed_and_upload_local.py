# embed_and_upload_local.py
import json
import re
from pathlib import Path
from tqdm import tqdm

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# -------- CONFIG -------
MOVIES_FILE = "movies_for_embedding.json"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "movies"
# Controls: total characters to allow per movie text (adjust to model/token budget)
MAX_CHARS_TOTAL = 4000
# If you want a smaller vector size (e.g. other model), update after loading the model.
MODEL_NAME = "all-mpnet-base-v2"
DISTANCE = rest.Distance.COSINE
# -----------------------

def split_parts(full_text: str):
    # expect "Tagline: ... Synopsis: ... Reviews: ...."
    # naive split: separate Reviews: part if present
    m = re.split(r"\bReviews:\s*", full_text, maxsplit=1)
    prefix = m[0] if m else ""
    reviews = m[1] if len(m) > 1 else ""
    return prefix.strip(), reviews.strip()

def truncate_keep_prefix(prefix: str, reviews: str, max_chars: int):
    # keep prefix full, then append as much of reviews as fits
    if len(prefix) + 1 + len(reviews) <= max_chars:
        return (prefix + (" " + reviews if reviews else "")).strip()
    else:
        allowed_for_reviews = max_chars - len(prefix) - 1
        if allowed_for_reviews <= 0:
            # prefix too long: hard truncate prefix (very rare)
            return prefix[:max_chars]
        truncated_reviews = reviews[:allowed_for_reviews]
        # avoid cutting mid-word if possible
        truncated_reviews = truncated_reviews.rsplit(" ", 1)[0]
        return (prefix + " " + truncated_reviews).strip()

def main():
    p = Path(MOVIES_FILE)
    assert p.exists(), f"{MOVIES_FILE} not found"

    records = json.loads(p.read_text(encoding="utf-8"))
    texts = []
    metas = []
    ids = []

    for rec in records:
        mid = rec.get("movie_id") or rec.get("metadata", {}).get("movie_id")
        txt = rec.get("text_for_embedding", "")
        meta = rec.get("metadata", {})
        prefix, reviews = split_parts(txt)
        final_text = truncate_keep_prefix(prefix, reviews, MAX_CHARS_TOTAL)
        ids.append(mid)
        texts.append(final_text)
        metas.append(meta)

    print("Loading embedding model:", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    # encode in batches
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32, convert_to_numpy=True)

    # prepare Qdrant
    client = QdrantClient(url=QDRANT_URL)
    vector_size = embeddings.shape[1]
    print("Vector size:", vector_size)

    # (re)create collection
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=rest.VectorParams(size=vector_size, distance=DISTANCE)
    )

    # upsert points in batches
    BATCH = 128
    points = []
    for i, (mid, vec, meta) in enumerate(zip(ids, embeddings, metas)):
        payload = meta or {}
        payload.update({"movie_id": mid})
        points.append(rest.PointStruct(id=i, vector=vec.tolist(), payload=payload))
        if len(points) >= BATCH:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            points = []
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    print("✅ Uploaded", len(ids), "vectors to Qdrant collection:", COLLECTION_NAME)

if __name__ == "__main__":
    main()
