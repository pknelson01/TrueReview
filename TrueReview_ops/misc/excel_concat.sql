/*
=CONCAT("INSERT INTO watched_list(user_id, movie_id, rating) VALUES (1, ", ROW()-1, ", """, SUBSTITUTE(A2, """", """"""), """, ", C2, ");")
*/