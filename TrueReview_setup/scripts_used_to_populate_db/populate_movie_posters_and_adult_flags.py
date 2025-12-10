import sqlite3
import requests
import threading
import time
import queue

TMDB_API_KEY = "9ca5e832beb93b3371c78a5fbc2280dc"
DB_FILE = "TrueReview.db"

BASE_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

REQUEST_DELAY = 0.20   # 5 requests/sec safe for TMDb
NUM_THREADS = 10       # max safe concurrency


# ============================================================
# FETCH ONLY THE NECESSARY LIGHTWEIGHT FIELDS
# ============================================================
def fetch_movie_light(movie_id):
    """Fastest possible TMDb fetch: only poster + adult."""
    url = BASE_MOVIE_URL.format(movie_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=6)

        if r.status_code != 200:
            return None

        data = r.json()

        poster_path = data.get("poster_path")
        poster_full_url = IMAGE_BASE + poster_path if poster_path else None
        adult_flag = 1 if data.get("adult") else 0

        return poster_path, poster_full_url, adult_flag

    except Exception:
        return None


# ============================================================
# WORKER THREAD
# ============================================================
def worker():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    while True:
        movie_id = job_queue.get()
        try:
            # Fetch data as fast as possible
            result = fetch_movie_light(movie_id)

            if result is None:
                print(f"[MISS] {movie_id}")
            else:
                poster_path, poster_full_url, adult_flag = result

                # Update the DB
                cur.execute(
                    """
                    UPDATE all_movies
                    SET poster_path = ?, poster_full_url = ?, adult_01 = ?
                    WHERE movie_id = ?;
                    """,
                    (poster_path, poster_full_url, adult_flag, movie_id)
                )
                conn.commit()

                print(f"[OK] {movie_id} updated")

            time.sleep(REQUEST_DELAY)

        finally:
            job_queue.task_done()


# ============================================================
# MAIN SCRIPT
# ============================================================
if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get all movie IDs
    cur.execute("SELECT movie_id FROM all_movies")
    movie_ids = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"Updating posters + adult flag for {len(movie_ids)} movies...\n")

    # Prepare job queue
    job_queue = queue.Queue()

    # Start worker threads
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # Enqueue all IDs
    for movie_id in movie_ids:
        job_queue.put(movie_id)

    job_queue.join()

    print("\n🎉 Poster + adult_01 update complete!")
