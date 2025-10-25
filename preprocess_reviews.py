# preprocess_reviews.py
import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict

INPUT = "reviews.json"
OUT_CLEAN = "reviews_cleaned.json"      # full structured output
OUT_MAP = "reviews_map.json"            # movie_id -> combined_reviews (single string)
OUT_FLAT = "reviews_flat.csv"           # each cleaned review as a row

# Configuration
MIN_REVIEW_CHARS = 15       # drop reviews shorter than this
MAX_REVIEWS_PER_MOVIE = None  # set to int to limit reviews per movie (None = keep all)
TRUNCATION_PATTERNS = [r"\.\.\.Read all$", r"\.\.\. Read all$", r"\.{3}Read all$"]  # patterns to strip

# ---------- helper functions ----------
def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    # common imdb truncation artifacts like "...Read all"
    for pat in TRUNCATION_PATTERNS:
        s = re.sub(pat, "", s, flags=re.IGNORECASE).strip()
    # remove HTML tags
    s = re.sub(r"<[^>]+>", " ", s)
    # fix escaped newlines and repeated whitespace
    s = s.replace("\\n", " ").replace("\\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    # remove stray unicode control chars
    s = "".join(ch for ch in s if ord(ch) >= 32 or ch == "\n")
    return s

def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# ---------- load ----------
p = Path(INPUT)
if not p.exists():
    raise FileNotFoundError(f"{INPUT} not found in current directory.")

with p.open("r", encoding="utf-8") as f:
    data = json.load(f)

if "movies" not in data or not isinstance(data["movies"], list):
    raise ValueError("Input JSON expected to contain top-level key 'movies' with a list.")

# ---------- process ----------
cleaned_movies = []
reviews_map: Dict[str, str] = {}
flat_rows = []

for movie in data["movies"]:
    movie_id = movie.get("movie_id") or movie.get("imdb_id") or movie.get("id")
    if not movie_id:
        # skip malformed entries
        continue

    reviews = movie.get("reviews") or []
    seen_hashes = set()
    cleaned_list: List[Dict] = []

    for r in reviews:
        # support different shapes
        review_id = r.get("review_id") or r.get("id") or None
        raw = r.get("comment") or r.get("text") or r.get("review") or ""
        txt = clean_text(raw)

        if len(txt) < MIN_REVIEW_CHARS:
            continue

        h = hash_text(txt)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        cleaned_item = {
            "review_id": review_id or h[:16],
            "text": txt
        }
        cleaned_list.append(cleaned_item)
        flat_rows.append({
            "movie_id": movie_id,
            "review_id": cleaned_item["review_id"],
            "text": txt
        })

    # optionally cap number of reviews per movie (keep longest or earliest)
    if MAX_REVIEWS_PER_MOVIE is not None and len(cleaned_list) > MAX_REVIEWS_PER_MOVIE:
        # keep longest reviews (heuristic)
        cleaned_list = sorted(cleaned_list, key=lambda x: -len(x["text"]))[:MAX_REVIEWS_PER_MOVIE]

    combined_reviews = " ".join([r["text"] for r in cleaned_list])

    cleaned_movies.append({
        "movie_id": movie_id,
        "reviews_raw": cleaned_list,
        "combined_reviews": combined_reviews,
        "review_count": len(cleaned_list)
    })
    reviews_map[movie_id] = combined_reviews

# ---------- save outputs ----------
with open(OUT_CLEAN, "w", encoding="utf-8") as f:
    json.dump({"movies": cleaned_movies}, f, ensure_ascii=False, indent=2)

with open(OUT_MAP, "w", encoding="utf-8") as f:
    json.dump(reviews_map, f, ensure_ascii=False, indent=2)

# write flat CSV
import csv
with open(OUT_FLAT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["movie_id", "review_id", "text"])
    writer.writeheader()
    for row in flat_rows:
        writer.writerow(row)

print(f"Saved cleaned reviews -> {OUT_CLEAN}")
print(f"Saved movie->combined mapping -> {OUT_MAP}")
print(f"Saved flat reviews CSV -> {OUT_FLAT}")
