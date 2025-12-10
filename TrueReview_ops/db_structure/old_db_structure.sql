CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, --link to watched_list
    username TEXT NOT NULL UNIQUE,
    bio TEXT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    title TEXT, 
    created_at TEXT DEFAULT (CURRENT_TIMESTAMP)
) STRICT;

CREATE TABLE IF NOT EXISTS watched_list (
	watched_id INTEGER PRIMARY KEY AUTOINCREMENT, 
	movie_id INTEGER NOT NULL, --link to all_movies by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_title TEXT NOT NULL, --Must be the same as the title in the all_movies table with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_genre TEXT NOT NULL, --Must be the same as the genre in the all_movies with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_runtime INTEGER NOT NULL, --Must be the same as the RUNTIME in the all_movies with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_rating TEXT NOT NULL, --Must be the same as the rating in the all_movies with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_language TEXT NOT NULL, --Must be the same as the LANGUAGE in the all_movies with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	movie_release_date TEXT NOT NULL --Must be the same as the RELEASE DATE in the all_movies with the movie_id by just the movie_id. When I insert into this table I should just have to insert the movie_id and the ret of the columns from the all_movies table will auto_populate
	user_id INTEGER NOT NULL, 
    user_rating REAL NOT NULL,              
    review TEXT,
    memory TEXT,
    watched_date TEXT,
    in_theater INTEGER,
    recommend INTEGER,
    rewatch_qty INTEGER,
) STRICT;

CREATE TABLE IF NOT EXISTS all_movies (
	movie_id INTEGER PRIMARY KEY,
	movie_title TEXT NOT NULL,
	movie_genre TEXT NOT NULL,
	movie_runtime INTEGER NOT NULL,
	movie_rating TEXT NOT NULL,
	movie_language TEXT NOT NULL,
	movie_release_date TEXT NOT NULL
)