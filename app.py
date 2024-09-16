import streamlit as st
import pickle
import requests
import os

st.title('Movie Recommendation System')

# Function to download similarity.pkl from a URL
def download_file(url, local_path):
    if not os.path.exists(local_path):
        st.info(f"Downloading {local_path}...")
        r = requests.get(url)
        with open(local_path, 'wb') as f:
            f.write(r.content)
        st.success(f"{local_path} downloaded successfully!")

# URL of the similarity.pkl file in your cloud storage
SIMILARITY_URL = "https://drive.google.com/file/d/1bNdCccWY5LPscIVAjt2BmLzXKc0a5aww/view"

# Define the local paths
SIMILARITY_LOCAL_PATH = 'similarity.pkl'

# Download the similarity.pkl file if it doesn't exist locally
download_file(SIMILARITY_URL, SIMILARITY_LOCAL_PATH)

# Load the movies and similarity matrix
movies = pickle.load(open('movies.pkl', 'rb'))
movies_title = movies['title'].values
similarity = pickle.load(open(SIMILARITY_LOCAL_PATH, 'rb'))

def fetch_poster(movie_id):
    try:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=6b2ccec43e41102d31886e12994af77d&language=en-US')
        data = response.json()
        return "https://image.tmdb.org/t/p/w500" + data['poster_path']
    except Exception as e:
        print(f"Error fetching poster: {e}")
        return "https://imgs.search.brave.com/I_jJEsHQuR6AzffdglWWC8VluqSBI-nd28u7H3zw8VM/rs:fit:500:0:0:0/g:ce/aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vcGhvdG8vMjAxNy8wMy8xMy8wNy8yOC9jb21tdW5pY2F0aW9uLTIxMzg5ODBfNjQwLmpwZw"

def recommended(movie):
    movie_index = movies[movies['title'] == movie].index.tolist()[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id

        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters

selected_movie = st.selectbox('Search for your Movies:', movies_title)

if st.button('Recommend'):
    names, posters = recommended(selected_movie)
    st.write("Recommended Movies:")

    cols = st.columns(5)

    for i in range(10):
        col_index = i % 5
        with cols[col_index]:
            st.image(posters[i])
            st.text(names[i])