import sqlite3
import csv

DB_PATH = "TrueReview.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def find_movie_id(title, year):
    # Try exact match first
    cursor.execute("""
        SELECT movie_id FROM all_movies
        WHERE lower(movie_title) = lower(?)
    """, (title,))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Try partial match + year if available
    cursor.execute("""
        SELECT movie_id FROM all_movies
        WHERE lower(movie_title) LIKE lower(?) 
    """, ('%' + title + '%',))
    row = cursor.fetchone()
    return row[0] if row else None


with open("watched.csv", newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        title = row["name"]
        year = row["year"]
        rating = row["rating"]
        director = row["director"]
        oscar_award = row["oscar_award"]
        oscar_01 = row["oscar_01"]

        movie_id = find_movie_id(title, year)

        if movie_id is None:
            print(f"⚠️ Movie not found in all_movies: {title} ({year})")
            continue

        cursor.execute("""
            INSERT INTO watched_list (movie_id, user_id, user_rating, review, memory, in_theater, recommend, rewatch_qty)
            VALUES (?, 1, ?, ?, ?, NULL, ?, NULL)
        """, (movie_id, rating, director, oscar_award, oscar_01))

        print(f"Inserted: {title} → movie_id {movie_id}")

conn.commit()
conn.close()

print("\nDone inserting watched movies!")
