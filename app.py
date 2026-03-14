import streamlit as st
import pickle
import requests
import gdown
import os

st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("🎬 Movie Recommendation System")

# -----------------------------
# Download similarity model
# -----------------------------

SIMILARITY_URL = "https://drive.google.com/uc?id=1_eDHLqcniMOPMkqTBwDOWOJutZVq8RsI"
SIMILARITY_LOCAL_PATH = "similarity.pkl"

if not os.path.exists(SIMILARITY_LOCAL_PATH):
    st.info("Downloading similarity model (~367MB)... Please wait.")
    gdown.download(SIMILARITY_URL, SIMILARITY_LOCAL_PATH, quiet=False)
    st.success("Download completed!")

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

        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]

        return "https://cdni.iconscout.com/illustration/premium/thumb/data-not-found-illustration-svg-download-png-9404367.png"

    except:
        return "https://learn.getgrav.org/user/pages/17/11.troubleshooting/01.page-not-found/404-not-found.png"
        

# -----------------------------
# Recommendation function
# -----------------------------
def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        key=lambda x: x[1],
        reverse=True
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