import spotipy

MOOD_TO_GENRES = {
    "chill": ["chill", "ambient", "lo-fi"],
    "energetic": ["dance", "edm", "electropop"],
    "sad": ["sad", "acoustic", "singer-songwriter"],
    "focus": ["study", "ambient", "classical"],
    "party": ["party", "dance", "hip-hop"],
    "workout": ["work-out", "edm", "hip-hop"],
    "melancholic": ["sad", "indie", "singer-songwriter"],
    "upbeat": ["pop", "dance", "happy"],
}

def get_spotify_client(access_token: str):
    return spotipy.Spotify(auth=access_token)


def search_tracks_by_mood(sp: spotipy.Spotify, mood: str, limit: int = 10) -> list:
    genres = MOOD_TO_GENRES.get(mood.lower(), [mood])
    tracks_per_genre = max(1, limit // len(genres))
    
    track_uris = []
    for genre in genres:
        results = sp.search(q=f'genre:{genre}', type="track", limit=tracks_per_genre)
        for track in results["tracks"]["items"]:
            track_uris.append(track["uri"])
        
    return track_uris[:limit]


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