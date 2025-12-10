console.log("Update Movie page loaded.");

const watchedId = window.location.pathname.split("/").pop();

// Load existing watched entry details
async function loadWatchedEntry() {
    const res = await fetch(`/api/watched/${watchedId}`);

    if (!res.ok) {
        console.error("Failed to load watched entry");
        return;
    }

    const data = await res.json();

    // Fill movie visuals
    document.getElementById("movie-poster").src = data.poster_full_url;
    document.getElementById("movie-title").textContent = data.movie_title;
    document.getElementById("movie-year").textContent = data.releaseYear;

    // Pre-fill rating + review
    document.getElementById("rating").value = data.user_rating;
    document.getElementById("review").value = data.review || "";

    // Set form actions
    document.getElementById("update-form").action = `/update-movie/${watchedId}`;
    document.getElementById("delete-form").action = `/delete-movie/${watchedId}`;
}

loadWatchedEntry();
