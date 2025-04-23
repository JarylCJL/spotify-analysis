import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
from dotenv import load_dotenv

# === Load credentials from .env ===
load_dotenv(dotenv_path=os.path.join("private", ".env"))

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

SCOPE = "playlist-read-private playlist-read-collaborative"

# === Step 2: Authenticate ===
def get_spotify_client():
    """Returns an authenticated Spotify API client using OAuth."""
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
    return sp

# === Step 3: Get User's Playlists ===
def get_user_playlists(sp):
    """Returns a dict of {playlist name: playlist id}."""
    playlists = sp.current_user_playlists()
    return {item["name"]: item["id"] for item in playlists["items"]}

# === Step 4: Get All Tracks from a Playlist ===
def fetch_playlist_tracks(sp, playlist_id):
    """Fetches all track objects from the selected playlist."""
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results["items"])
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks

# === Step 5: Extract Audio Features ===
def extract_audio_features(sp, playlist_id):
    """
    Fetches all tracks from the playlist and returns a DataFrame
    with key audio features for each song.
    """
    tracks = fetch_playlist_tracks(sp, playlist_id)
    data = []
    for item in tracks:
        track = item["track"]
        if not track or not track["id"]:
            continue

        audio = sp.audio_features(track["id"])[0]
        if audio:
            data.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "tempo": audio["tempo"],
                "energy": audio["energy"],
                "danceability": audio["danceability"],
                "valence": audio["valence"],
                "acousticness": audio["acousticness"],
                "instrumentalness": audio["instrumentalness"],
                "liveness": audio["liveness"],
                "speechiness": audio["speechiness"],
                "loudness": audio["loudness"],
                "key": audio["key"],
                "mode": "Major" if audio["mode"] == 1 else "Minor"
            })

    return pd.DataFrame(data)

# === Step 6: Run standalone ===
if __name__ == "__main__":
    sp = get_spotify_client()
    print("Fetching your playlists...")
    playlists = get_user_playlists(sp)

    for i, name in enumerate(playlists):
        print(f"{i+1}. {name}")

    choice = int(input("Select a playlist by number: ")) - 1
    playlist_id = list(playlists.values())[choice]
    playlist_name = list(playlists.keys())[choice]

    print(f"\nExtracting audio features from '{playlist_name}'...")
    df = extract_audio_features(sp, playlist_id)

    out_path = f"../data/{playlist_name.replace(' ', '_')}_audio_features.csv"
    df.to_csv(out_path, index=False)
    print(f"\n✅ Saved to {out_path}")
