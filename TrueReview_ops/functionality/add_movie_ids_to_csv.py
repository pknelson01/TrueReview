import pandas as pd
import requests
import time

TMDB_API_KEY = "9ca5e832beb93b3371c78a5fbc2280dc"

INPUT_CSV = "/Users/parkernelson/Desktop/work/TrueReview_DB/LetterBoxd_data/letterboxd-tholt0-2025-12-08-22-36-utc/ratings.csv"

OUTPUT_CSV = "/Users/parkernelson/Desktop/work/TrueReview_DB/movies_with_ids(Tiana).csv"

SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

def fetch_movie_id(Name):
    """Search TMDb for the movie Name and return the best movie_id match."""
    params = {
        "api_key": TMDB_API_KEY,
        "query": Name,
        "include_adult": False
    }

    try:
        r = requests.get(SEARCH_URL, params=params, timeout=5)
        data = r.json()

        results = data.get("results", [])
        if not results:
            return None

        # Return the first (best) TMDb result
        return results[0].get("id")

    except Exception as e:
        print(f"Error fetching '{Name}': {e}")
        return None


def main():
    df = pd.read_csv(INPUT_CSV)

    if "Name" not in df.columns:
        raise ValueError("CSV must contain a 'Name' column.")

    movie_ids = []

    print("\nFetching TMDb IDs...\n")

    for Name in df["Name"]:
        movie_id = fetch_movie_id(Name)
        movie_ids.append(movie_id)
        print(f"{Name}  →  {movie_id}")

        time.sleep(0.25)   # prevent rate-limit issues

    df["movie_id"] = movie_ids

    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nDone! Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
