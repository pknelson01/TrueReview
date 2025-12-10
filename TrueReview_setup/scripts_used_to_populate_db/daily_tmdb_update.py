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

REQUEST_DELAY = 0.20  # 5 requests/sec (safe)

# ============================================================
# FETCH MOVIE DETAILS
# ============================================================
def fetch_movie(movie_id):
    """Fetch main movie content from TMDb."""
    url = BASE_MOVIE_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return None

        data = response.json()

        movie_title = data.get("title", "")
        movie_runtime = data.get("runtime") or 0
        movie_language = data.get("original_language", "")
        movie_release_date = data.get("release_date") or ""

        genres = data.get("genres", [])
        movie_genre = ", ".join(g["name"] for g in genres) if genres else "Unknown"

        # Poster fields
        poster_path = data.get("poster_path")
        poster_full_url = IMAGE_BASE + poster_path if poster_path else None

        # Adult flag
        adult_flag = 1 if data.get("adult") else 0

        # MPAA rating (separate API)
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
            "adult_flag": adult_flag
        }

    except Exception:
        return None


# ============================================================
# FETCH MPAA RATING
# ============================================================
def fetch_mpaa(movie_id):
    url = BASE_RATING_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return "NR"

        for country in response.json().get("results", []):
            if country.get("iso_3166_1") == "US":
                for release in country.get("release_dates", []):
                    cert = release.get("certification")
                    if cert:
                        return cert

        return "NR"

    except Exception:
        return "NR"


# ============================================================
# WORKER THREAD — adds OR updates movie data
# ============================================================
def worker():
    local_conn = sqlite3.connect(DB_FILE)
    local_cursor = local_conn.cursor()

    while True:
        movie_id = movie_queue.get()
        try:
            data = fetch_movie(movie_id)

            if data:
                # Insert OR update
                local_cursor.execute("""
                    INSERT INTO all_movies (
                        movie_id, movie_title, movie_genre, movie_runtime,
                        mpaa_rating, movie_language, movie_release_date,
                        poster_path, poster_full_url, adult_01
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(movie_id) DO UPDATE SET
                        movie_title=excluded.movie_title,
                        movie_genre=excluded.movie_genre,
                        movie_runtime=excluded.movie_runtime,
                        mpaa_rating=excluded.mpaa_rating,
                        movie_language=excluded.movie_language,
                        movie_release_date=excluded.movie_release_date,
                        poster_path=excluded.poster_path,
                        poster_full_url=excluded.poster_full_url,
                        adult_01=excluded.adult_01
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
                    data["adult_flag"]
                ))

                local_conn.commit()
                print(f"[OK] {movie_id} — {data['movie_title']}")

            else:
                print(f"[MISS] {movie_id}")

            time.sleep(REQUEST_DELAY)

        finally:
            movie_queue.task_done()


# ============================================================
# MAIN UPDATE SCRIPT
# ============================================================
if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure full schema exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_movies (
            movie_id INTEGER PRIMARY KEY,
            movie_title TEXT NOT NULL,
            movie_genre TEXT NOT NULL,
            movie_runtime INTEGER NOT NULL,
            mpaa_rating TEXT NOT NULL,
            movie_language TEXT NOT NULL,
            movie_release_date TEXT NOT NULL,
            poster_path TEXT,
            poster_full_url TEXT,
            adult_01 INTEGER
        ) STRICT;
    """)
    conn.commit()

    # Load existing movie IDs
    cursor.execute("SELECT movie_id FROM all_movies")
    existing = {row[0] for row in cursor.fetchall()}
    conn.close()

    START = 1
    END = 1_000_000

    print(f"{len(existing)} movies already in DB.")
    print("Building update list...")

    # Daily update list:
    # 1. Fill missing IDs
    # 2. Refresh all existing movies (posters, adult flag, updated metadata)
    update_list = list(range(START, END + 1))

    print(f"Updating {len(update_list)} movie IDs...\n")

    # Thread queue
    movie_queue = queue.Queue()

    NUM_THREADS = 10
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # Queue all IDs
    for movie_id in update_list:
        movie_queue.put(movie_id)

    movie_queue.join()
    print("\n🎉 DAILY TMDB UPDATE COMPLETE!")
