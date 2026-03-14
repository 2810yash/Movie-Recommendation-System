# mrs-movies
 Movie Recommendation System

## Run locally

1. `pip install -r requirements.txt`
2. `streamlit run app.py`

## Posters (TMDB)

To enable posters, set `TMDB_API_KEY` as an environment variable or in `.streamlit/secrets.toml` (or set `TMDB_API_KEY` at the top of `app.py` like your old version):

```toml
TMDB_API_KEY="your_key_here"
```