import users
import movie
import imports
import requests
from config import TMDB_API_KEY

def fetch_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

movie = fetch_movie(550)
print(f"Title: {movie['original_title']}\nMovie ID: {movie['id']}")
