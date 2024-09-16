import streamlit as st
import pickle
import requests

st.title('Movie Recommendation System')

# Load the movies and similarity matrix
movies = pickle.load(open('movies.pkl', 'rb'))
movies_title = movies['title'].values
similarity = pickle.load(open('similarity.pkl', 'rb'))

def fetch_poster(movie_id):
    try:
        response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=6b2ccec43e41102d31886e12994af77d&language=en-US'.format(movie_id))
        data = response.json()
        return "https://image.tmdb.org/t/p/w500" + data['poster_path']
    except Exception as e:
        print(f"Error fetching poster: {e}")
        return "https://imgs.search.brave.com/I_jJEsHQuR6AzffdglWWC8VluqSBI-nd28u7H3zw8VM/rs:fit:500:0:0:0/g:ce/aHR0cHM6Ly9jZG4u/cGl4YWJheS5jb20v/cGhvdG8vMjAxNy8w/My8xMy8wNy8yOC9j/b21tdW5pY2F0aW9u/LTIxMzg5ODBfNjQw/LmpwZw"

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
