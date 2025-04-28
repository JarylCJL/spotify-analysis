import os
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from typing import List, Dict

# === Load Spotify credentials from private/.env ===
# Assumes this file is at spotify_playlist_analysis/src/spotify_utils.py
env_path = Path(__file__).resolve().parent.parent / "private" / ".env"
load_dotenv(dotenv_path=env_path)

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SCOPE = "playlist-read-private playlist-read-collaborative"


def get_spotify_client() -> spotipy.Spotify:
    """
    Authenticate via OAuth and return a Spotify client.
    """
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def list_user_playlists(sp: spotipy.Spotify, limit: int = 50) -> pd.DataFrame:
    """
    Retrieve current user's playlists and return as a DataFrame with columns:
      - id: playlist ID
      - name: playlist name
      - track_count: number of tracks in playlist
    """
    playlists: List[Dict] = []
    response = sp.current_user_playlists(limit=limit)
    while response:
        for item in response["items"]:
            playlists.append({
                "id": item["id"],
                "name": item["name"],
                "track_count": item["tracks"]["total"]
            })
        if response.get("next"):
            response = sp.next(response)
        else:
            break
    return pd.DataFrame(playlists)


def get_playlist_track_ids(sp: spotipy.Spotify, playlist_id: str) -> List[str]:
    """
    Fetch all track IDs from the specified playlist.
    """
    track_ids: List[str] = []
    response = sp.playlist_items(
        playlist_id,
        fields="items.track.id,next",
        additional_types=["track"]
    )
    while response:
        for item in response["items"]:
            track = item.get("track")
            if track and track.get("id"):
                track_ids.append(track["id"])
        if response.get("next"):
            response = sp.next(response)
        else:
            break
    return track_ids


def get_audio_features(sp: spotipy.Spotify, track_ids: List[str]) -> pd.DataFrame:
    """
    Retrieve audio features for a list of track IDs and return as a DataFrame.
    """
    features_list: List[Dict] = []
    # Spotify API allows max 100 IDs per request; using 50 for safety
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i + 50]
        features = sp.audio_features(batch)
        for f in features:
            if f:
                features_list.append(f)
    return pd.DataFrame(features_list)


def fetch_and_save_playlist_analysis(playlist_id: str, output_path: str) -> pd.DataFrame:
    """
    Complete pipeline: fetch track IDs, retrieve audio features, and save to CSV.

    Args:
        playlist_id: Spotify playlist ID to analyze.
        output_path: File path for the output CSV (e.g. data/playlist.csv).

    Returns:
        DataFrame of audio features.
    """
    sp = get_spotify_client()
    ids = get_playlist_track_ids(sp, playlist_id)
    features_df = get_audio_features(sp, ids)
    # Ensure output directory exists
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(out_file, index=False)
    return features_df


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Analyze a Spotify playlist and save audio features.')
    parser.add_argument('playlist_id', help='Spotify playlist ID')
    parser.add_argument('--output', default='../data/playlist_analysis.csv', help='CSV output path')
    args = parser.parse_args()
    df = fetch_and_save_playlist_analysis(args.playlist_id, args.output)
    print(f"Saved {len(df)} track features to {args.output}.")
