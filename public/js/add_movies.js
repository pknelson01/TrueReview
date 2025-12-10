// =============================================================================
//  add_movies.js — Client-side rendering for Add Movie page
// =============================================================================

const searchInput = document.getElementById("movie-search");
const resultsDiv = document.getElementById("search-results");
const loadingText = document.getElementById("loading-text");
const errorText = document.getElementById("error-text");

let debounceTimer = null;

// -----------------------------------------------------------------------------
//  RENDER RESULTS INTO HTML
// -----------------------------------------------------------------------------
function renderResults(movies) {
    resultsDiv.innerHTML = "";

    if (!movies || movies.length === 0) {
        resultsDiv.innerHTML = `<p class="no-results">No movies found.</p>`;
        return;
    }

    movies.forEach(movie => {
        const card = document.createElement("div");
        card.className = "movie-card";

        card.innerHTML = `
            <img class="poster" src="${movie.poster_full_url}" alt="${movie.movie_title}" />

            <div class="movie-info">
                <h2 class="title">${movie.movie_title}</h2>
                <p class="year">${movie.isCurrentYear ? movie.fullReleaseDate : movie.releaseYear}</p>

                <a href="/rate-movie/${movie.movie_id}" class="select-btn">Select</a>
            </div>
        `;

        resultsDiv.appendChild(card);
    });
}

// -----------------------------------------------------------------------------
//  FETCH SEARCH RESULTS
// -----------------------------------------------------------------------------
async function searchMovies(query) {
    if (!query.trim()) {
        resultsDiv.innerHTML = "";
        return;
    }

    loadingText.style.display = "block";
    errorText.style.display = "none";

    try {
        // IMPORTANT: Your backend route is /api/search-movies
        const res = await fetch(`/api/search-movies?q=${encodeURIComponent(query)}`);

        if (!res.ok) throw new Error("Bad response");

        const movies = await res.json();
        
        loadingText.style.display = "none";
        renderResults(movies);

    } catch (err) {
        loadingText.style.display = "none";
        errorText.style.display = "block";
        console.error("Search Error:", err);
    }
}

// -----------------------------------------------------------------------------
//  DEBOUNCE INPUT
// -----------------------------------------------------------------------------
searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        searchMovies(searchInput.value);
    }, 300);
});
