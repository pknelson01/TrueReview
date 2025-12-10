select u.username, am.movie_title as "Favorite Movie", wl.movie_id from users u
join watched_list wl on u.user_id = wl.user_id
join all_movies am on am.movie_id = wl.movie_id
where u.user_id = 1
and wl.movie_id = u.favorite_movie;