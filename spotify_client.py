import spotipy

def get_spotify_client(access_token: str):
    return spotipy.Spotify(auth=access_token)


def search_tracks_by_mood(sp: spotipy.Spotify, mood: str, limit: int = 10) -> list:
    results = sp.search(q=mood, type="track", limit=limit)
    
    track_uris = []
    
    for track in results["tracks"]["items"]:
        track_uris.append(track["uri"])
        
    return track_uris


def create_playlist(sp: spotipy.Spotify, name: str, description: str = "", public: bool = True) -> str:
    payload = {
        "name": name,
        "public": public,
        "description": description
    }
    
    playlist = sp._post("me/playlists", payload=payload)
    playlist_id = playlist["id"]
    
    return playlist_id


def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: list) -> None:
    sp.playlist_add_items(playlist_id, track_uris)