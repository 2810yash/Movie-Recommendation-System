import streamlit as st
import pickle
import requests
import os

st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("🎬 Movie Recommendation System")

# -----------------------------
# Download similarity file safely
# -----------------------------
def download_file(url, local_path):
    if not os.path.exists(local_path):
        st.info("Downloading similarity model (~367MB). Please wait...")

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        st.success("Model downloaded successfully!")

SIMILARITY_URL = "https://drive.google.com/uc?export=download&id=1_eDHLqcniMOPMkqTBwDOWOJutZVq8RsI"
SIMILARITY_LOCAL_PATH = "similarity.pkl"

download_file(SIMILARITY_URL, SIMILARITY_LOCAL_PATH)

# -----------------------------
# Load data with caching
# -----------------------------
@st.cache_resource
def load_data():
    movies = pickle.load(open("movies.pkl", "rb"))
    similarity = pickle.load(open("similarity.pkl", "rb"))
    return movies, similarity

movies, similarity = load_data()
movies_title = movies["title"].values

# -----------------------------
# Fetch movie poster
# -----------------------------
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=6b2ccec43e41102d31886e12994af77d&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get("poster_path")

        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            return "https://via.placeholder.com/500x750?text=No+Image"

    except:
        return "https://via.placeholder.com/500x750?text=Error"

# -----------------------------
# Recommendation function
# -----------------------------
def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    recommended_movies = []
    recommended_posters = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters

# -----------------------------
# UI
# -----------------------------
selected_movie = st.selectbox("Search for a movie", movies_title)

if st.button("Recommend 🎥"):

    names, posters = recommend(selected_movie)

    st.subheader("Recommended Movies")

    cols = st.columns(5)

    for i in range(10):
        with cols[i % 5]:
            st.image(posters[i])
            st.caption(names[i])