"""
classify_reviews.py

Loads scraped RMP reviews, cleans them, and applies zero-shot
classification (facebook/bart-large-mnli) to score each review against
a fixed set of teaching-related aspects. Produces a per-professor
aspect profile.
"""

import pandas as pd
from tqdm import tqdm
from transformers import pipeline

ASPECTS = [
    "harsh grading",
    "great teaching",
    "poor teaching",
    "engaging lectures",
    "boring lectures",
    "heavy workload",
    "approachable and kind",
    "unavailable or unhelpful",
]


def load_and_clean(path: str) -> pd.DataFrame:
    """Load scraped reviews and drop empty/very short comments."""
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} raw reviews")

    df = df.dropna(subset=["comment"])
    df = df[df["comment"].str.len() > 10]
    print(f"{len(df)} reviews remain after cleaning")

    return df


def build_classifier():
    """Load the zero-shot classification pipeline."""
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def classify_review(classifier, comment: str) -> dict:
    """Score a single review comment against the fixed aspect list."""
    try:
        result = classifier(comment, ASPECTS, multi_label=True)
        return dict(zip(result["labels"], result["scores"]))
    except Exception:
        return {}


def classify_all(df: pd.DataFrame, classifier) -> pd.DataFrame:
    """Apply classification to every review and attach the scores as columns."""
    tqdm.pandas()
    df["aspect_scores"] = df["comment"].progress_apply(
        lambda comment: classify_review(classifier, comment)
    )

    scores_df = pd.json_normalize(df["aspect_scores"])
    return pd.concat([df, scores_df], axis=1)


def build_professor_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Average aspect scores per professor to build a per-professor profile."""
    return df.groupby("professor")[ASPECTS].mean().reset_index()


def main():
    df = load_and_clean("rmp_reviews.csv")

    classifier = build_classifier()
    df_scored = classify_all(df, classifier)
    df_scored.to_csv("rmp_reviews_scored.csv", index=False)
    print("Saved scored reviews to rmp_reviews_scored.csv")

    profiles = build_professor_profiles(df_scored)
    profiles.to_csv("professor_profiles.csv", index=False)
    print("Saved per-professor aspect profiles to professor_profiles.csv")


if __name__ == "__main__":
    main()