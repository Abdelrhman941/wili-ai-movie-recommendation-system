import pandas as pd
import json

print("🔹 Loading files...")
movies_df = pd.read_csv("movies_preprocessed.csv", encoding="utf-8").fillna("")
with open("reviews_map.json", "r", encoding="utf-8") as f:
    reviews_map = json.load(f)

print("🔹 Columns in movies_preprocessed.csv:", list(movies_df.columns))

# Normalize column names
movies_df.columns = [col.strip().lower() for col in movies_df.columns]

# Map reviews
movies_df["combined_reviews"] = movies_df["imdb_id"].map(reviews_map).fillna("")

# --- Build text_for_embedding ---
def build_text_for_embedding(row):
    parts = []
    tagline = str(row.get("tagline", "")).strip()
    synopsis = str(row.get("synopsis", "")).strip()
    reviews = str(row.get("combined_reviews", "")).strip()

    if tagline:
        parts.append(f"Tagline: {tagline}")
    if synopsis:
        parts.append(f"Synopsis: {synopsis}")
    if reviews:
        parts.append(f"Reviews: {reviews}")

    return " ".join(parts).strip()

print("🔹 Building text_for_embedding...")
movies_df["text_for_embedding"] = movies_df.apply(build_text_for_embedding, axis=1)

# --- Build metadata ---
def build_metadata(row):
    return {
        "movie_id": row.get("imdb_id", ""),
        "title": row.get("title", ""),
        "genre": row.get("genres_list", ""),
        "rating": row.get("weighted_rating", ""),
        "release_date": row.get("release_date", ""),
        "runtime_min": row.get("runtime_mins", ""),
        "url": row.get("imdb_url", "")
    }

movies_df["metadata"] = movies_df.apply(build_metadata, axis=1)

# --- Final output ---
movies_for_embedding = movies_df[["imdb_id", "text_for_embedding", "metadata"]].rename(columns={"imdb_id": "movie_id"})

output_file = "movies_for_embedding.json"
print(f"🔹 Saving merged file → {output_file}")

movies_for_embedding.to_json(output_file, orient="records", indent=2, force_ascii=False)

print("✅ Done! Successfully created movies_for_embedding.json")
