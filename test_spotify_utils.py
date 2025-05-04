# test_spotify_utils.py
from src.spotify_utils import (
    get_spotify_client,
    get_user_playlists,
    fetch_playlist_tracks,
    fetch_audio_features,
    get_playlist_with_features,
)

def test_user_playlists():
    sp = get_spotify_client()
    df = get_user_playlists(sp)
    print("▶️ Your playlists:")
    print(df.head(), "\n")

def test_playlist_tracks():
    sp = get_spotify_client()
    playlists = get_user_playlists(sp)
    if playlists.empty:
        print("No playlists found.")
        return
    pid = playlists["id"].iloc[0]
    tracks = fetch_playlist_tracks(sp, pid)
    print(f"▶️ First 5 tracks from playlist {playlists['name'].iloc[0]}:")
    print(tracks.head(), "\n")

def test_audio_features():
    sp = get_spotify_client()
    # swap in any valid track ID here
    sample = ["47isJpIIO8m7BJEhiFhnaf"]
    feats = fetch_audio_features(sp, sample)
    print("▶️ Audio features for one track:")
    print(feats, "\n")

def test_playlist_with_features():
    df = get_playlist_with_features(
        get_user_playlists(get_spotify_client())["id"].iloc[0]
    )
    print("▶️ Combined DataFrame (tracks + features):")
    print(df.head(), "\n")

if __name__ == "__main__":
    test_user_playlists()
    test_playlist_tracks()
    test_audio_features()
    test_playlist_with_features()
