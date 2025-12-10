// ============================================================================
//  SERVER.JS — TrueReview (HTML VERSION, NO EJS)
// ============================================================================

import express from "express";
import session from "express-session";
import path from "path";
import multer from "multer";
import pg from "pg";
import { fileURLToPath } from "url";

// ----------------------------------------------------
// Path Fix (ESM)
// ----------------------------------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ----------------------------------------------------
// Express Setup
// ----------------------------------------------------
const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ----------------------------------------------------
// Static Files
// ----------------------------------------------------
app.use("/public", express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static(path.join(__dirname, "uploads")));
app.use("/views", express.static(path.join(__dirname, "views")));

// ----------------------------------------------------
// Sessions
// ----------------------------------------------------
app.use(
  session({
    secret: "truereview_secret_123",
    resave: false,
    saveUninitialized: false,
  })
);

// ----------------------------------------------------
// PostgreSQL Setup
// ----------------------------------------------------
const db = new pg.Pool({
  connectionString:
    "postgresql://truereview_admin:TrNMyIlmWQqxTBtiownOkjAPiNGT6bK6@dpg-d4qhtuh5pdvs738o9d90-a.oregon-postgres.render.com/truereview",
  ssl: { rejectUnauthorized: false },
});

// ----------------------------------------------------
// Multer (File Uploads)
// ----------------------------------------------------
const profilePicStorage = multer.diskStorage({
  destination: "./uploads/profile_pictures",
  filename: (req, file, cb) => {
    cb(
      null,
      `pfp_${req.session.user_id}_${Date.now()}${path.extname(
        file.originalname
      )}`
    );
  },
});

const backgroundStorage = multer.diskStorage({
  destination: "./uploads/profile_backgrounds",
  filename: (req, file, cb) => {
    cb(
      null,
      `bg_${req.session.user_id}_${Date.now()}${path.extname(
        file.originalname
      )}`
    );
  },
});

const uploadProfilePic = multer({ storage: profilePicStorage });
const uploadBackground = multer({ storage: backgroundStorage });

// ----------------------------------------------------
// Auth Middleware
// ----------------------------------------------------
function requireLogin(req, res, next) {
  if (!req.session.user_id) return res.redirect("/login");
  next();
}

// ============================================================================
// ROUTES — HTML PAGES
// ============================================================================

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "views/index.html"));
});

app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "views/login.html"));
});

// LOGIN USING EMAIL + PASSWORD
app.post("/login", async (req, res) => {
  const { email, password } = req.body;

  const sql = `
    SELECT * FROM users
    WHERE email = $1 AND password = $2
  `;

  const result = await db.query(sql, [email, password]);

  if (result.rows.length === 0) {
    return res.redirect("/login?error=1");
  }

  req.session.user_id = result.rows[0].user_id;
  res.redirect("/welcome");
});

app.post("/logout", (req, res) => {
  req.session.destroy(() => res.redirect("/"));
});

app.get("/welcome", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/welcome.html"));
});

app.get("/dashboard", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/dashboard.html"));
});

// ============================================================================
// API — DASHBOARD DATA
// ============================================================================
app.get("/api/dashboard", requireLogin, async (req, res) => {
  const user_id = req.session.user_id;

  const userQ = `
    SELECT username, title, bio, profile_picture, profile_background_photo, favorite_movie
    FROM users WHERE user_id = $1
  `;
  const user = (await db.query(userQ, [user_id])).rows[0];

  const followQ = `
    SELECT  
      COUNT(f_followers.follower_id) AS follower_count,
      COUNT(f_following.following_id) AS following_count
    FROM users u
    LEFT JOIN user_follows f_followers
      ON u.user_id = f_followers.following_id
    LEFT JOIN user_follows f_following
      ON u.user_id = f_following.follower_id
    WHERE u.user_id = $1
    GROUP BY u.user_id
  `;
  const follow = (await db.query(followQ, [user_id])).rows[0] || {
    follower_count: 0,
    following_count: 0,
  };

  const statsQ = `
    SELECT COUNT(*) AS total_movies,
           ROUND(AVG(user_rating)::numeric, 2) AS avg_rating
    FROM watched_list 
    WHERE user_id = $1
  `;
  const stats = (await db.query(statsQ, [user_id])).rows[0];

  const favQ = `
    SELECT am.movie_title
    FROM users u
    JOIN all_movies am ON am.movie_id = u.favorite_movie
    WHERE u.user_id = $1
  `;
  const fav = await db.query(favQ, [user_id]);
  const favorite_movie_title = fav.rows.length ? fav.rows[0].movie_title : null;

  const lastQ = `
    SELECT wl.user_rating, am.movie_title, am.poster_full_url
    FROM watched_list wl
    JOIN all_movies am ON wl.movie_id = am.movie_id
    WHERE wl.user_id = $1
    ORDER BY wl.watched_id DESC LIMIT 1
  `;
  const last = (await db.query(lastQ, [user_id])).rows[0];

  res.json({
    user,
    follower_count: follow.follower_count,
    following_count: follow.following_count,
    total_movies: stats.total_movies,
    avg_rating: stats.avg_rating,
    favorite_movie_title,
    last,
  });
});

// ============================================================================
// MOVIES
// ============================================================================

// Serve Add Movie Page
app.get("/add-movie", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/add_movies.html"));
});

// SEARCH MOVIES (JSON API)
app.get("/api/search-movies", requireLogin, async (req, res) => {
  const q = req.query.q || "";

  const sql = `
    SELECT movie_id, movie_title, poster_full_url, movie_release_date
    FROM all_movies
    WHERE movie_title ILIKE $1
    ORDER BY movie_title
    LIMIT 50
  `;

  const rows = (await db.query(sql, [`%${q}%`])).rows;

  res.json(
    rows.map((m) => {
      const d = new Date(m.movie_release_date);
      return {
        ...m,
        releaseYear: d.getFullYear(),
        isCurrentYear: d.getFullYear() === new Date().getFullYear(),
        fullReleaseDate: d.toLocaleDateString(),
      };
    })
  );
});

// ⭐⭐⭐ FETCH A SINGLE MOVIE (for user rating page)
app.get("/api/movie/:id", requireLogin, async (req, res) => {
  const id = req.params.id;

  const sql = `
    SELECT movie_id, movie_title, poster_full_url, movie_release_date
    FROM all_movies
    WHERE movie_id = $1
  `;

  const result = await db.query(sql, [id]);

  if (result.rows.length === 0) {
    return res.status(404).json({ error: "Movie not found" });
  }

  const m = result.rows[0];
  const d = new Date(m.movie_release_date);

  res.json({
    ...m,
    releaseYear: d.getFullYear(),
  });
});

// Serve Update Movie Page (HTML)
app.get("/update-movie/:id", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/update_movie.html"));
});

// Serve Rate Movie Page (HTML)
app.get("/rate-movie/:id", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/rate_movie.html"));
});

// Add Movie Rating
app.post("/add-movie/:id", requireLogin, async (req, res) => {
  const user_id = req.session.user_id;
  const movie_id = req.params.id;
  const { rating, review } = req.body;

  const sql = `
    INSERT INTO watched_list (user_id, movie_id, user_rating, review)
    VALUES ($1, $2, $3, $4)
  `;

  await db.query(sql, [user_id, movie_id, rating, review || null]);
  res.redirect("/dashboard");
});

// ============================================================================
// ⭐⭐⭐ NEW: WATCHED PAGE + WATCHED APIs
// ============================================================================

// Serve Watched Page
app.get("/watched", requireLogin, (req, res) => {
  res.sendFile(path.join(__dirname, "views/watched.html"));
});

// Fetch list of watched movies
app.get("/api/watched", requireLogin, async (req, res) => {
  const user_id = req.session.user_id;

  const sql = `
    SELECT wl.watched_id, wl.user_rating, am.movie_title, am.poster_full_url
    FROM watched_list wl
    JOIN all_movies am ON wl.movie_id = am.movie_id
    WHERE wl.user_id = $1
    ORDER BY wl.watched_id DESC
  `;

  const rows = (await db.query(sql, [user_id])).rows;
  res.json(rows);
});

// ⭐⭐⭐ FETCH A SINGLE WATCHED ENTRY (used in update page)
app.get("/api/watched/:id", requireLogin, async (req, res) => {
  const watched_id = req.params.id;
  const user_id = req.session.user_id;

  const sql = `
    SELECT wl.watched_id, wl.user_rating, wl.review,
           am.movie_title, am.poster_full_url, am.movie_release_date
    FROM watched_list wl
    JOIN all_movies am ON wl.movie_id = am.movie_id
    WHERE wl.watched_id = $1 AND wl.user_id = $2
  `;

  const result = await db.query(sql, [watched_id, user_id]);

  if (result.rows.length === 0) {
    return res.status(404).json({ error: "Entry not found" });
  }

  const m = result.rows[0];
  const d = new Date(m.movie_release_date);

  res.json({
    ...m,
    releaseYear: d.getFullYear(),
  });
});

// ⭐⭐⭐ UPDATE an existing watched entry
app.post("/update-movie/:id", requireLogin, async (req, res) => {
  const watched_id = req.params.id;
  const user_id = req.session.user_id;
  const { rating, review } = req.body;

  const sql = `
    UPDATE watched_list
    SET user_rating = $1,
        review = $2
    WHERE watched_id = $3 AND user_id = $4
  `;

  await db.query(sql, [rating, review, watched_id, user_id]);
  res.redirect("/watched");
});

// ⭐⭐⭐ DELETE a watched entry
app.post("/delete-movie/:id", requireLogin, async (req, res) => {
  const watched_id = req.params.id;
  const user_id = req.session.user_id;

  const sql = `
    DELETE FROM watched_list
    WHERE watched_id = $1 AND user_id = $2
  `;

  await db.query(sql, [watched_id, user_id]);
  res.redirect("/watched");
});

// ============================================================================
// START SERVER
// ============================================================================
const PORT = 3000;
app.listen(PORT, () =>
  console.log(`TrueReview running at http://localhost:${PORT}`)
);
