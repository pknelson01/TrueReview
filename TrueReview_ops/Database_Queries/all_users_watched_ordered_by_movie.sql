select u.username, wl.user_id, wl.user_rating, am.movie_title, wl.movie_id from watched_list wl 
join users u
on u.user_id = wl.user_id
join all_movies am 
on wl.movie_id = am.movie_id
where u.user_id >= 1
order by am.movie_id;