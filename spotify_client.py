import spotipy


def get_spotify_client(access_token: str):
    return spotipy.Spotify(auth=access_token)


def search_tracks_by_queries(sp: spotipy.Spotify, queries: list[str], limit: int = 10) -> list:
    tracks_per_query = max(1, limit // len(queries))
    
    track_uris = []
    for query in queries:
        results = sp.search(q=query, type="track", limit=tracks_per_query)
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