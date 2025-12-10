console.log("Watched page loaded.");

async function loadWatched() {
    try {
        const res = await fetch("/api/watched");
        const movies = await res.json();

        const grid = document.querySelector(".movies-grid");
        grid.innerHTML = ""; // Clear template

        if (movies.length === 0) {
            grid.innerHTML = `<p class="empty-msg">You haven't watched any movies yet.</p>`;
            return;
        }

        movies.forEach(movie => {
            const card = document.createElement("a");
            card.href = `/update-movie/${movie.watched_id}`;
            card.className = "movie-card";

            card.innerHTML = `
                <div class="poster-wrapper">
                    <img 
                        src="${movie.poster_full_url}" 
                        alt="${movie.movie_title}" 
                        class="movie-poster"
                    >

                    <div class="hover-overlay">
                        <h2 class="movie-title">${movie.movie_title}</h2>
                        <p class="user-rating">Your Rating: ${movie.user_rating}/5</p>
                    </div>
                </div>
            `;

            grid.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading watched movies:", err);
    }
}

// Load immediately
loadWatched();
