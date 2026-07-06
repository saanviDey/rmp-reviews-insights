"""
scrape_reviews.py

Scrapes professor and review data from Rate My Professors via their
public GraphQL API, for a given school, and saves the results to CSV.
"""

import requests
import pandas as pd
from tqdm import tqdm

RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"

# RMP's public-facing GraphQL endpoint expects this placeholder basic-auth
# header (decodes to "test:test") rather than a real credential.
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.ratemyprofessors.com/",
}


def _post_graphql(query: str, variables: dict) -> dict:
    """Send a GraphQL query to RMP and return the parsed JSON response."""
    payload = {"query": query, "variables": variables}
    response = requests.post(RMP_GRAPHQL_URL, json=payload, headers=HEADERS)
    data = response.json()

    if "errors" in data:
        print("GraphQL errors:", data["errors"])

    return data


def get_school_id(school_name: str) -> list:
    """Search RMP for a school by name and return matching school nodes."""
    query = """
    query SchoolSearchQuery($query: SchoolSearchQuery!) {
        newSearch {
            schools(query: $query) {
                edges {
                    node {
                        id
                        name
                        city
                        state
                    }
                }
            }
        }
    }
    """
    data = _post_graphql(query, {"query": {"text": school_name}})

    if "data" not in data:
        return []

    schools = data["data"]["newSearch"]["schools"]["edges"]
    for school in schools:
        print(school["node"])

    return schools


def get_professors(school_id: str, num_professors: int = 1000) -> pd.DataFrame:
    """Fetch professors at a given school ID."""
    query = """
    query TeacherSearchQuery($schoolID: ID!, $count: Int!) {
        newSearch {
            teachers(query: {schoolID: $schoolID}, first: $count) {
                edges {
                    node {
                        id
                        firstName
                        lastName
                        department
                        avgRating
                        avgDifficulty
                        numRatings
                    }
                }
            }
        }
    }
    """
    data = _post_graphql(query, {"schoolID": school_id, "count": num_professors})

    if "data" not in data:
        return pd.DataFrame()

    professors = [edge["node"] for edge in data["data"]["newSearch"]["teachers"]["edges"]]
    return pd.DataFrame(professors)


def get_reviews(professor_id: str, num_reviews: int = 20) -> pd.DataFrame:
    """Fetch reviews for a single professor by ID."""
    query = """
    query RatingsListQuery($id: ID!, $count: Int!) {
        node(id: $id) {
            ... on Teacher {
                firstName
                lastName
                ratings(first: $count) {
                    edges {
                        node {
                            comment
                            qualityRating
                            difficultyRatingRounded
                            date
                            class
                            thumbsUpTotal
                            thumbsDownTotal
                        }
                    }
                }
            }
        }
    }
    """
    data = _post_graphql(query, {"id": professor_id, "count": num_reviews})

    node = data.get("data", {}).get("node")
    if node is None:
        print(f"No data found for professor ID: {professor_id}")
        return pd.DataFrame()

    reviews = []
    for edge in node["ratings"]["edges"]:
        r = edge["node"]
        r["professor"] = f"{node['firstName']} {node['lastName']}"
        reviews.append(r)

    return pd.DataFrame(reviews)


def scrape_all_reviews(df_profs: pd.DataFrame, num_reviews: int = 20,
                        min_ratings: int = 5) -> pd.DataFrame:
    """Loop over every professor and collect their reviews into one DataFrame."""
    all_reviews = []

    for _, prof in tqdm(df_profs.iterrows(), total=len(df_profs)):
        if prof["numRatings"] < min_ratings:
            continue

        try:
            reviews = get_reviews(prof["id"], num_reviews=num_reviews)
            reviews["department"] = prof["department"]
            reviews["avgRating"] = prof["avgRating"]
            all_reviews.append(reviews)
        except Exception as e:
            print(f"Failed for {prof['firstName']}: {e}")
            continue

    return pd.concat(all_reviews, ignore_index=True)


def main():
    school_results = get_school_id("Purdue University West Lafayette")
    if not school_results:
        raise SystemExit("Could not find school ID — check the school name.")

    school_id = school_results[0]["node"]["id"]

    df_profs = get_professors(school_id, num_professors=500)
    print(df_profs.head())

    df_all = scrape_all_reviews(df_profs, num_reviews=20, min_ratings=5)
    df_all.to_csv("rmp_reviews.csv", index=False)
    print(f"Collected {len(df_all)} reviews across {len(df_profs)} professors")


if __name__ == "__main__":
    main()