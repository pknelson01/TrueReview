import requests
import sqlite3
import threading
import time
import queue

TMDB_API_KEY = "9ca5e832beb93b3371c78a5fbc2280dc"

# ✅ USE ABSOLUTE PATH — NEVER FAILS
DB_FILE = "/Users/parkernelson/Desktop/work/TrueReview/TrueReview.db"

BASE_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
BASE_RATING_URL = "https://api.themoviedb.org/3/movie/{}/release_dates"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

REQUEST_DELAY = 0.20      # 5 req/sec (safe global limit)
NUM_THREADS = 10          # ~50 req/sec across threads = safe


# ============================================================
# FETCH US MPAA RATING
# ============================================================
def fetch_mpaa(movie_id):
    url = BASE_RATING_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return "NR"

        results = r.json().get("results", [])

        for country in results:
            if country.get("iso_3166_1") == "US":
                for rel in country.get("release_dates", []):
                    cert = rel.get("certification")
                    if cert:
                        return cert

        return "NR"

    except:
        return "NR"


# ============================================================
# FETCH MOVIE METADATA (excluding adult films)
# ============================================================
def fetch_movie(movie_id):
    url = BASE_MOVIE_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None  # invalid or missing ID

        data = r.json()

        # EXCLUDE ADULT FILMS COMPLETELY
        if data.get("adult") is True:
            return None

        movie_title = data.get("title", "")
        movie_runtime = data.get("runtime") or 0
        movie_language = data.get("original_language", "")
        movie_release_date = data.get("release_date") or ""

        genres = data.get("genres", [])
        movie_genre = ", ".join(g["name"] for g in genres) if genres else "Unknown"

        # Poster URLs
        poster_path = data.get("poster_path")
        poster_full_url = IMAGE_BASE + poster_path if poster_path else None

        # MPAA rating
        mpaa_rating = fetch_mpaa(movie_id)

        return {
            "movie_id": movie_id,
            "movie_title": movie_title,
            "movie_genre": movie_genre,
            "movie_runtime": movie_runtime,
            "mpaa_rating": mpaa_rating,
            "movie_language": movie_language,
            "movie_release_date": movie_release_date,
            "poster_path": poster_path,
            "poster_full_url": poster_full_url,
            "adult_01": 0  # ALWAYS 0 because adults are excluded
        }

    except Exception:
        return None


# ============================================================
# WORKER THREAD
# ============================================================
def worker():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    while True:
        movie_id = movie_queue.get()

        try:
            data = fetch_movie(movie_id)

            if data:
                cur.execute("""
                    INSERT OR IGNORE INTO all_movies (
                        movie_id, movie_title, movie_genre, movie_runtime,
                        mpaa_rating, movie_language, movie_release_date,
                        poster_path, poster_full_url, adult_01
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["movie_id"],
                    data["movie_title"],
                    data["movie_genre"],
                    data["movie_runtime"],
                    data["mpaa_rating"],
                    data["movie_language"],
                    data["movie_release_date"],
                    data["poster_path"],
                    data["poster_full_url"],
                    data["adult_01"]
                ))
                conn.commit()
                print(f"[OK] {movie_id} — {data['movie_title']}")

            else:
                print(f"[SKIP] {movie_id}")

            time.sleep(REQUEST_DELAY)

        finally:
            movie_queue.task_done()


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    START_ID = 1_438_069
    END_ID = 1_594_354

    movie_queue = queue.Queue()

    print(f"Scraping TMDb IDs from {START_ID} → {END_ID} (adult excluded).")

    # Start threads
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # Queue all movie IDs
    for movie_id in range(START_ID, END_ID + 1):
        movie_queue.put(movie_id)

    movie_queue.join()
    print("\n🎉 FINISHED SCRAPING 1,400,000 → 1,594,354")
