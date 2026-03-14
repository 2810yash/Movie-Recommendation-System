import difflib
import os
import pickle
from pathlib import Path
from typing import Optional

import gdown
import requests
import streamlit as st


st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("Movie Recommendation System")
st.caption("Pick a movie you like and get similar recommendations.")

# -----------------------------
# Files / config
# -----------------------------

MOVIES_LOCAL_PATH = "movies.pkl"
SIMILARITY_LOCAL_PATH = "similarity.pkl"

SIMILARITY_URL = "https://drive.google.com/uc?id=1_eDHLqcniMOPMkqTBwDOWOJutZVq8RsI"

# Put your TMDB key here (works like your old code), or leave blank and set it via env/secrets.
# Safer options:
# - Environment variable: TMDB_API_KEY="..."
# - Streamlit secrets: .streamlit/secrets.toml with TMDB_API_KEY="..."
TMDB_API_KEY = "6b2ccec43e41102d31886e12994af77d"
TMDB_API_KEY_NAME = "TMDB_API_KEY"

POSTER_FALLBACK_URL = (
    "https://cdni.iconscout.com/illustration/premium/thumb/data-not-found-illustration-svg-download-png-9404367.png"
)


def _get_tmdb_api_key() -> Optional[str]:
    if TMDB_API_KEY.strip():
        return TMDB_API_KEY.strip()

    env_key = os.getenv(TMDB_API_KEY_NAME, "").strip()
    if env_key:
        return env_key

    # Avoid Streamlit warning spam: only touch st.secrets if a secrets.toml exists.
    secrets_paths = [
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ]
    if not any(p.exists() for p in secrets_paths):
        return None

    try:
        key = st.secrets.get(TMDB_API_KEY_NAME)
    except Exception:
        return None

    key = str(key).strip() if key else ""
    return key or None


def _ensure_similarity_file() -> None:
    if os.path.exists(SIMILARITY_LOCAL_PATH):
        return

    st.info("Downloading similarity model (~367MB)... Please wait.")
    try:
        gdown.download(SIMILARITY_URL, SIMILARITY_LOCAL_PATH, quiet=False)
    except Exception as exc:
        st.error(f"Download failed: {exc}")
        st.stop()
    st.success("Download completed!")


@st.cache_resource
def _http_session() -> requests.Session:
    return requests.Session()


@st.cache_resource
def load_data():
    _ensure_similarity_file()

    if not os.path.exists(MOVIES_LOCAL_PATH):
        raise FileNotFoundError(MOVIES_LOCAL_PATH)

    with open(MOVIES_LOCAL_PATH, "rb") as f:
        movies = pickle.load(f)
    with open(SIMILARITY_LOCAL_PATH, "rb") as f:
        similarity = pickle.load(f)

    return movies, similarity


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _fetch_poster_by_tmdb_id(tmdb_movie_id: int) -> str:
    api_key = _get_tmdb_api_key()
    if not api_key:
        return POSTER_FALLBACK_URL

    try:
        resp = _http_session().get(
            f"https://api.themoviedb.org/3/movie/{tmdb_movie_id}",
            params={"api_key": api_key, "language": "en-US"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return POSTER_FALLBACK_URL

    poster_path = data.get("poster_path")
    if not poster_path:
        return POSTER_FALLBACK_URL

    return "https://image.tmdb.org/t/p/w500" + poster_path


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _fetch_poster_by_imdb_id(imdb_id: str) -> str:
    api_key = _get_tmdb_api_key()
    if not api_key:
        return POSTER_FALLBACK_URL

    try:
        resp = _http_session().get(
            f"https://api.themoviedb.org/3/find/{imdb_id}",
            params={"api_key": api_key, "external_source": "imdb_id"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return POSTER_FALLBACK_URL

    results = data.get("movie_results") or data.get("tv_results") or []
    if not results:
        return POSTER_FALLBACK_URL

    poster_path = results[0].get("poster_path")
    if not poster_path:
        return POSTER_FALLBACK_URL

    return "https://image.tmdb.org/t/p/w500" + poster_path


def fetch_poster(movie_id) -> str:
    # Accept TMDB numeric IDs or IMDb IDs like "tt1234567".
    if movie_id is None:
        return POSTER_FALLBACK_URL

    if isinstance(movie_id, int):
        return _fetch_poster_by_tmdb_id(movie_id)

    raw = str(movie_id).strip()
    if not raw:
        return POSTER_FALLBACK_URL

    if raw.lower().startswith("tt"):
        return _fetch_poster_by_imdb_id(raw)

    try:
        return _fetch_poster_by_tmdb_id(int(raw))
    except Exception:
        return POSTER_FALLBACK_URL


def recommend(movies_df, similarity_matrix, movie_title: str, top_k: int):
    matches = movies_df.index[movies_df["title"] == movie_title].tolist()
    if not matches:
        return [], []

    movie_index = matches[0]
    distances = similarity_matrix[movie_index]

    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)
    ranked = [x for x in ranked if x[0] != movie_index][: max(0, int(top_k))]

    recommended_movies = []
    recommended_posters = []
    for idx, _score in ranked:
        mid = movies_df.iloc[idx].movie_id
        recommended_movies.append(str(movies_df.iloc[idx].title))
        recommended_posters.append(fetch_poster(mid))

    return recommended_movies, recommended_posters


try:
    movies, similarity = load_data()
except FileNotFoundError as exc:
    st.error(f"Missing required file: {exc.filename}")
    st.stop()
except Exception as exc:
    st.error(f"Failed to load model/data: {exc}")
    st.stop()

movies_title = movies["title"].astype(str).tolist()

# -----------------------------
# UI (hybrid: clean + details)
# -----------------------------

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")
    query = st.text_input("Search title", placeholder="Type to filter...")

    filtered_titles = movies_title
    if query.strip():
        q = query.strip().lower()
        filtered_titles = [t for t in movies_title if q in t.lower()]
        if not filtered_titles:
            filtered_titles = difflib.get_close_matches(query.strip(), movies_title, n=25, cutoff=0.55)

    if not filtered_titles:
        st.warning("No matching titles found.")
        st.stop()

    selected_movie = st.selectbox("Pick a movie", filtered_titles, index=0)
    top_k = st.slider("Recommendations", 5, 20, 10)
    grid_cols = st.slider("Grid columns", 2, 6, 5)
    show_description = st.checkbox("Show description", value=True)

if not _get_tmdb_api_key():
    st.warning("Posters disabled: set TMDB_API_KEY (env/secrets) or fill TMDB_API_KEY in app.py.")

selected_row = movies[movies["title"] == selected_movie].head(1)
selected_movie_id = selected_row.iloc[0].movie_id if not selected_row.empty else None
selected_tags = str(selected_row.iloc[0].tags) if (show_description and not selected_row.empty) else ""

left, right = st.columns([1, 2])

with left:
    st.subheader("Selected movie")
    if selected_movie_id is not None:
        st.image(fetch_poster(selected_movie_id), use_column_width=True)
    st.caption(selected_movie)

with right:
    st.subheader("Details")
    if selected_tags:
        st.write(selected_tags[:420] + ("..." if len(selected_tags) > 420 else ""))
    clicked = st.button("Recommend", type="primary")

if clicked:
    with st.spinner("Finding similar movies..."):
        names, posters = recommend(movies, similarity, selected_movie, top_k=top_k)

    if not names:
        st.error("Could not generate recommendations for that title.")
        st.stop()

    st.subheader("Recommended movies")
    cols = st.columns(int(grid_cols))
    for i, (name, poster) in enumerate(zip(names, posters)):
        with cols[i % int(grid_cols)]:
            st.image(poster, use_column_width=True)
            st.caption(name)