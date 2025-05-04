import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

# === Load credentials from .env ===
# Assumes private/.env contains SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
load_dotenv()  # Automatically looks for .env in current working directory

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Scopes to read user playlists
SCOPE = "playlist-read-private playlist-read-collaborative"


def get_spotify_client():
    """
    Authenticate and return a Spotify client using OAuth2 for user-specific endpoints.
    """
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_app_client():
    """
    Return a Spotify client using Client Credentials flow for public endpoints like audio-features.
    """
    creds = SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return spotipy.Spotify(client_credentials_manager=creds)


def get_user_playlists(sp: spotipy.Spotify) -> pd.DataFrame:
    """
    Retrieve current user's playlists (paginated) and return DataFrame of name & id.
    """
    playlists = []
    results = sp.current_user_playlists(limit=50)
    playlists.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])

    return pd.DataFrame([
        {'name': p['name'], 'id': p['id']}
        for p in playlists
    ])


def fetch_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> pd.DataFrame:
    """
    Retrieve all tracks in the given playlist ID and return DataFrame of basic track info.
    """
    tracks = []
    results = sp.playlist_items(
        playlist_id,
        fields='items.track.id,items.track.name,items.track.artists.name,items.track.album.name,next',
        additional_types=['track']
    )
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    records = []
    for item in tracks:
        track = item['track']
        records.append({
            'track_id': track['id'],
            'track_name': track['name'],
            'artist': ', '.join([a['name'] for a in track['artists']]),
            'album': track['album']['name'],
        })
    return pd.DataFrame(records)


def fetch_audio_features(sp: spotipy.Spotify, track_ids: list[str]) -> pd.DataFrame:
    """
    Fetch audio features for up to 50 tracks per request using the app client.
    """
    sp_app = get_app_client()
    features = []
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        features.extend(sp_app.audio_features(batch))
    return pd.DataFrame(features)


def get_playlist_with_features(playlist_id: str) -> pd.DataFrame:
    """
    Wrapper: fetch track list for the playlist, then fetch and merge audio features.
    """
    sp = get_spotify_client()
    playlist_df = fetch_playlist_tracks(sp, playlist_id)
    if playlist_df.empty:
        return playlist_df

    feature_df = fetch_audio_features(sp, playlist_df['track_id'].tolist())
    combined = playlist_df.merge(feature_df, left_on='track_id', right_on='id', how='left')
    return combined
