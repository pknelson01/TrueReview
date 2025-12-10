import requests
import sqlite3
import threading
import time
import queue

TMDB_API_KEY = "9ca5e832beb93b3371c78a5fbc2280dc"
DB_FILE = "TrueReview.db"

BASE_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
BASE_RATING_URL = "https://api.themoviedb.org/3/movie/{}/release_dates"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

REQUEST_DELAY = 0.20     # 5 req/sec — safe limit
NUM_THREADS = 10         # ~50 req/sec total


# ============================================================
# BASIC API CHECK — Does movie_id exist?
# ============================================================
def exists(movie_id):
    url = BASE_MOVIE_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    r = requests.get(url, params=params)
    time.sleep(REQUEST_DELAY)

    return r.status_code == 200


# ============================================================
# STEP 1 — Find new upper bound & max valid ID
# ============================================================
def find_upper_bound(start=800_000):
    """Find an ID where TMDb stops having movies."""
    current = start
    print(f"🔍 Checking upper bound starting at {current}")

    while exists(current):
        print(f"  ✔ {current} exists — doubling")
        current *= 2
        if current > 5_000_000:
            break

    print(f"📌 Upper bound found: {current} (non-existing)")
    return current


def binary_search_max(low, high):
    """Binary search to find highest existing TMDb movie_id."""
    print(f"\n🔎 Binary searching {low} → {high}")

    while low < high:
        mid = (low + high + 1) // 2

        if exists(mid):
            low = mid
        else:
            high = mid - 1

        print(f"  Range now → {low} to {high}")

    print(f"\n🎉 New MAX TMDb movie_id = {low}\n")
    return low


# ============================================================
# STEP 2 — Fetch MPAA rating
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
            if country["iso_3166_1"] == "US":
                for rel in country["release_dates"]:
                    cert = rel.get("certification")
                    if cert:
                        return cert

        return "NR"
    except:
        return "NR"


# ============================================================
# STEP 3 — Fetch movie metadata (excluding adult films)
# ============================================================
def fetch_movie(movie_id):
    url = BASE_MOVIE_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None

        data = r.json()

        # 🚫 EXCLUDE ADULT FILMS
        if data.get("adult") is True:
            return None

        # Build movie object
        movie_title = data.get("title", "")
        movie_runtime = data.get("runtime") or 0
        movie_language = data.get("original_language", "")
        movie_release_date = data.get("release_date") or ""

        genres = data.get("genres", [])
        movie_genre = ", ".join(g["name"] for g in genres) if genres else "Unknown"

        poster_path = data.get("poster_path")
        poster_full_url = IMAGE_BASE + poster_path if poster_path else None

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
            "adult_01": 0
        }

    except:
        return None


# ============================================================
# STEP 4 — Worker thread
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
                    data["movie_id"], data["movie_title"], data["movie_genre"],
                    data["movie_runtime"], data["mpaa_rating"], data["movie_language"],
                    data["movie_release_date"], data["poster_path"],
                    data["poster_full_url"], data["adult_01"]
                ))

                conn.commit()
                print(f"[OK] {movie_id} — {data['movie_title']}")
            else:
                print(f"[SKIP] {movie_id}")

            time.sleep(REQUEST_DELAY)

        finally:
            movie_queue.task_done()


# ============================================================
# MAIN — WEEKLY UPDATE
# ============================================================
if __name__ == "__main__":
    print("\n===== WEEKLY TMDB SYNC STARTED =====\n")

    # 1. Load DB and get existing movie_ids
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT movie_id FROM all_movies")
    existing_ids = {row[0] for row in cur.fetchall()}

    print(f"📀 Database currently contains {len(existing_ids):,} movies.")

    # 2. Find latest TMDb ID range
    upper = find_upper_bound(start=1_000_000)
    max_id = binary_search_max(1, upper)

    print(f"📌 Updating database up to ID {max_id:,}")

    # 3. Build missing ID list
    full_range = set(range(1, max_id + 1))
    missing_ids = sorted(full_range - existing_ids)

    print(f"📌 Found {len(missing_ids):,} missing IDs to fill.\n")

    conn.close()

    # 4. Start worker threads
    movie_queue = queue.Queue()

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # 5. Fill in missing movies
    for movie_id in missing_ids:
        movie_queue.put(movie_id)

    movie_queue.join()

    print("\n🎉 WEEKLY TMDB SYNC COMPLETED — Database is now fully updated!\n")
