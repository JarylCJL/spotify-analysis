import streamlit as st
from src.spotify_utils import get_spotify_client, get_user_playlists, get_playlist_with_features
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_playlists():
    """Fetch and cache the current user’s playlists."""
    sp = get_spotify_client()
    return get_user_playlists(sp)

@st.cache_data
def load_playlist_data(playlist_id: str) -> pd.DataFrame:
    """Fetch and cache tracks + audio features for the selected playlist."""
    return get_playlist_with_features(playlist_id)


def main():
    st.set_page_config(page_title="Spotify Playlist Analyzer", layout="wide")
    st.title("🎧 Spotify Playlist Analyzer")

    # Sidebar: Playlist selection
    st.sidebar.header("Select Playlist")
    with st.sidebar.spinner("Loading your playlists..."):
        playlists_df = load_playlists()

    if playlists_df.empty:
        st.error("No playlists found for your account.")
        return

    playlist_map = playlists_df.set_index('name')['id'].to_dict()
    selected_name = st.sidebar.selectbox("Playlist", options=list(playlist_map.keys()))

    if st.sidebar.button("Load Playlist"):
        playlist_id = playlist_map[selected_name]
        with st.spinner(f"Fetching tracks for '{selected_name}'..."):
            df = load_playlist_data(playlist_id)

        if df.empty:
            st.warning("This playlist is empty.")
            return

        # Display raw data
        st.subheader(f"Tracks & Audio Features: {selected_name}")
        st.dataframe(
            df[
                ["track_name", "artist", "album", "danceability", "energy", "valence"]
            ]
        )

        # Mood map plot
        st.subheader("Mood Map: Valence vs Energy")
        fig, ax = plt.subplots()
        ax.scatter(df["valence"], df["energy"], alpha=0.7)
        ax.set_xlabel("Valence")
        ax.set_ylabel("Energy")
        ax.set_title("Mood Distribution of Tracks")
        st.pyplot(fig)

if __name__ == "__main__":
    main()
