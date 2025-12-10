const stars = document.querySelectorAll(".star");
const ratingInput = document.getElementById("rating-input");
const submitBtn = document.getElementById("submit-btn");

let currentRating = 0;

// Highlight stars on hover
stars.forEach(star => {
    star.addEventListener("mouseover", () => {
        const value = star.dataset.value;
        highlightStars(value);
    });

    // Restore to selected state when mouse leaves
    star.addEventListener("mouseout", () => {
        highlightStars(currentRating);
    });

    // On click, lock in rating
    star.addEventListener("click", () => {
        currentRating = star.dataset.value;
        ratingInput.value = currentRating;

        submitBtn.disabled = false;
        submitBtn.classList.add("enabled");

        highlightStars(currentRating);
    });
});

function highlightStars(value) {
    stars.forEach(star => {
        star.classList.remove("hovered", "selected");

        if (star.dataset.value <= value) {
            star.classList.add("selected");
        }
    });
}
