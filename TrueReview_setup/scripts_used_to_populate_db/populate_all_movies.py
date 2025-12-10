import requests
import sqlite3
import threading
import time
import queue

TMDB_API_KEY = "9ca5e832beb93b3371c78a5fbc2280dc"
DB_FILE = "TrueReview.db"

# ------------------------------------------------
# TMDb REQUEST FUNCTION
# ------------------------------------------------
def fetch_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        data = response.json()

        movie_title = data.get("title", "")
        movie_runtime = data.get("runtime") or 0
        movie_language = data.get("original_language", "")
        movie_release_date = data.get("release_date") or ""

        genres = data.get("genres", [])
        movie_genre = ", ".join(g["name"] for g in genres) if genres else "Unknown"

        mpaa_rating = fetch_mpaa(movie_id)

        return {
            "movie_id": movie_id,
            "movie_title": movie_title,
            "movie_genre": movie_genre,
            "movie_runtime": movie_runtime,
            "mpaa_rating": mpaa_rating,
            "movie_language": movie_language,
            "movie_release_date": movie_release_date
        }

    except Exception:
        return None


# ------------------------------------------------
# MPAA FETCH
# ------------------------------------------------
def fetch_mpaa(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={TMDB_API_KEY}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "NR"

        results = response.json().get("results", [])
        for country in results:
            if country.get("iso_3166_1") == "US":
                for release in country.get("release_dates", []):
                    cert = release.get("certification")
                    if cert:
                        return cert
        return "NR"

    except Exception:
        return "NR"


# ------------------------------------------------
# WORKER THREAD
# ------------------------------------------------
def worker():
    local_conn = sqlite3.connect(DB_FILE)
    local_cursor = local_conn.cursor()

    while True:
        movie_id = movie_queue.get()
        try:
            local_cursor.execute("SELECT 1 FROM all_movies WHERE movie_id = ?", (movie_id,))
            if local_cursor.fetchone():
                print(f"[SKIP] ID {movie_id} exists")
            else:
                data = fetch_movie(movie_id)
                
                if data:
                    local_cursor.execute("""
                        INSERT OR IGNORE INTO all_movies
                        (movie_id, movie_title, movie_genre, movie_runtime, mpaa_rating, movie_language, movie_release_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data["movie_id"],
                        data["movie_title"],
                        data["movie_genre"],
                        data["movie_runtime"],
                        data["mpaa_rating"],
                        data["movie_language"],
                        data["movie_release_date"]
                    ))

                    local_conn.commit()
                    print(f"[OK] Added {data['movie_title']} (ID {movie_id})")
                else:
                    print(f"[MISS] No data for ID {movie_id}")

            time.sleep(0.20)  # Respect TMDb rate limits

        finally:
            movie_queue.task_done()


# ------------------------------------------------
# MAIN LOGIC — FIND MISSING IDS
# ------------------------------------------------
if __name__ == "__main__":

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_movies (
            movie_id INTEGER PRIMARY KEY,
            movie_title TEXT NOT NULL,
            movie_genre TEXT NOT NULL,
            movie_runtime INTEGER NOT NULL,
            mpaa_rating TEXT NOT NULL,
            movie_language TEXT NOT NULL,
            movie_release_date TEXT NOT NULL
        ) STRICT;
    """)
    conn.commit()

    # Get all existing movie IDs
    cursor.execute("SELECT movie_id FROM all_movies")
    existing = {row[0] for row in cursor.fetchall()}

    START_ID = 1
    END_ID = 1_000_000  # You can update later if TMDb expands

    print(f"Found {len(existing)} movies already in DB.")
    print("Building list of missing IDs...")

    missing_ids = [i for i in range(START_ID, END_ID + 1) if i not in existing]

    print(f"{len(missing_ids)} missing movie IDs found.")
    conn.close()

    if not missing_ids:
        print("No missing movies! Database is complete.")
        exit()

    movie_queue = queue.Queue()

    NUM_THREADS = 10  # safe for TMDb limits

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    for movie_id in missing_ids:
        movie_queue.put(movie_id)

    movie_queue.join()
    print("Finished filling all missing movie entries.")
