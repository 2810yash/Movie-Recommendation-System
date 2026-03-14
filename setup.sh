mkdir -p ~/.streamlit/

# Streamlit reads server settings from config.toml (not credentials.toml).
cat > ~/.streamlit/config.toml <<EOF
[server]
port = ${PORT}
enableCORS = false
headless = true
EOF
