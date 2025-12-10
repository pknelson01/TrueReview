select
    u.user_id,
    u.username,
    count(f_followers.follower_id) as follower_count,
    count(f_following.following_id) as following_count
from users u
left join user_follows f_followers
    on u.user_id = f_followers.following_id
left join user_follows f_following
    on u.user_id = f_following.follower_id
group by u.user_id, u.username
order by follower_count desc;