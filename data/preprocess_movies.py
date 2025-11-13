# preprocess_movies.py
import pandas as pd
import re

# ========== 1. Load ==========
df = pd.read_csv("movies.csv")
print(f"Loaded {len(df)} movies")

# ========== 2. Canonicalize IMDb ID ==========
df["IMDb ID"] = df["IMDb ID"].astype(str).str.strip()
df = df.drop_duplicates(subset=["IMDb ID"])

# ========== 3. Filter titleType (keep only movies) ==========
if "titleType" in df.columns:
    df = df[df["titleType"].str.lower().isin(["movie", "feature", "film", "feature film"])]

# ========== 4. Clean release year and runtime ==========
# Release Date column actually holds release year, so treat it as numeric
if "Release Date" in df.columns:
    df["release_date"] = pd.to_numeric(df["Release Date"], errors="coerce").astype("Int64")

# Runtime
if "Runtime (minutes)" in df.columns:
    df["runtime_mins"] = pd.to_numeric(df["Runtime (minutes)"], errors="coerce")

# ========== 5. Clean textual fields ==========
text_cols = ["Movie_name", "Genre/s", "Synopsis", "Tagline"]

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"<.*?>", "", text)  # remove HTML tags
    text = re.sub(r"\s+", " ", text)   # collapse whitespace
    text = text.replace("\\n", " ").replace("\\", "")
    return text.strip()

for col in text_cols:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)

# ========== 6. Split genres to list ==========
if "Genre/s" in df.columns:
    def split_genres(genre_str):
        if not genre_str or pd.isna(genre_str):
            return []
        return [g.strip().lower() for g in genre_str.split(",") if g.strip()]
    df["genres_list"] = df["Genre/s"].apply(split_genres)

# ========== 7. Short summary ==========
def build_short_summary(row):
    if row.get("Tagline"):
        return row["Tagline"]
    synopsis = row.get("Synopsis", "")
    if synopsis:
        sentences = re.split(r'(?<=[.!?]) +', synopsis)
        return " ".join(sentences[:2])
    return ""

df["short_summary"] = df.apply(build_short_summary, axis=1)

# ========== 8. Trim long synopsis ==========
MAX_CHARS = 4000
df["Synopsis"] = df["Synopsis"].apply(lambda x: x[:MAX_CHARS] if len(x) > MAX_CHARS else x)

# ========== 9. Clean up + rename ==========
rename_map = {
    "IMDb ID": "imdb_id",
    "Movie_name": "title",
    "Weighted Average rating": "weighted_rating",
    "Weighted Average Count": "weighted_count",
    "IMDb URL": "imdb_url"
}
df.rename(columns=rename_map, inplace=True)

# Select relevant columns
keep_cols = [
    "imdb_id", "title", "titleType", "release_date", "runtime_mins",
    "genres_list", "Synopsis", "Tagline", "short_summary",
    "weighted_rating", "weighted_count", "imdb_url"
]
df_final = df[[col for col in keep_cols if col in df.columns]]

# ========== 10. Save ==========
df_final.to_csv("movies_preprocessed.csv", index=False)
print(f"✅ Saved cleaned file with {len(df_final)} movies → movies_preprocessed.csv")
