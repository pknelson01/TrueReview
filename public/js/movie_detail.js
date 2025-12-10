// STAR RATING LOGIC
const stars = document.querySelectorAll(".star");
const ratingInput = document.getElementById("rating-input");

let currentRating = ratingInput.value;

// Hover + select behavior
stars.forEach(star => {
    star.addEventListener("mouseover", () => {
        highlight(star.dataset.value);
    });

    star.addEventListener("mouseout", () => {
        highlight(currentRating);
    });

    star.addEventListener("click", () => {
        currentRating = star.dataset.value;
        ratingInput.value = currentRating;
        highlight(currentRating);
    });
});

function highlight(value) {
    stars.forEach(s => {
        s.classList.remove("selected");
        if (s.dataset.value <= value) s.classList.add("selected");
    });
}

// UNWATCH CONFIRMATION MODAL
const unwatchBtn = document.getElementById("unwatch-btn");
const modal = document.getElementById("modal-overlay");
const cancelBtn = document.getElementById("cancel-btn");

unwatchBtn.addEventListener("click", () => {
    modal.classList.add("active");
});

cancelBtn.addEventListener("click", () => {
    modal.classList.remove("active");
});
