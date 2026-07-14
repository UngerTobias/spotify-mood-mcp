from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from auth import get_auth_url, exchange_code_for_tokens
from db import init_db, save_tokens, get_tokens

from mcp.server.fastmcp import FastMCP

from spotify_client import get_spotify_client, search_tracks_by_mood, create_playlist, add_tracks_to_playlist
from auth import refresh_access_token

import time

app = FastAPI()
mcp = FastMCP("spotify-mood")

init_db()

@app.get("/login/{user_id}")
def login(user_id: str):
    url = get_auth_url(user_id)
    return RedirectResponse(url)


@app.get("/callback")
def callback(code: str, state: str):
    tokens = exchange_code_for_tokens(code)
    save_tokens(state, tokens["access_token"], tokens["refresh_token"], tokens["expires_at"])
    
    return {"message": "Verbindung zu Spotify hergestellt. Kehre nun zu Claude zurück!"}


@mcp.tool()
def create_mood_playlist(user_id: str, mood: str, description: str) -> str:
    """
    Erstellt eine neue Spotify-Playlist für einen bestimmten Nutzer, passend zu einer Stimmung.

    WICHTIG - user_id ermitteln:
    Falls du für diese Person noch keinen gespeicherten Namen/user_id kennst
    (z.B. aus dem bisherigen Gesprächsverlauf oder deinem Gedächtnis), frag sie
    einmalig: "Wie soll ich dich intern nennen, damit ich deine Spotify-Verbindung
    wiedererkenne?" und merke dir die Antwort für zukünftige Gespräche mit dieser Person.
    Nutze exakt diesen Namen als user_id bei jedem weiteren Aufruf dieses Tools.

    Falls die Funktion zurückgibt, dass der Nutzer nicht verbunden ist: teile ihr/ihm
    mit, dass er/sie einmalig auf http://<server-url>/login/<user_id> gehen muss
    (mit genau der user_id, die ihr gerade festgelegt habt), um Claude einmalig mit
    Spotify zu verbinden.

    Args:
        user_id: Ein eindeutiger, selbstgewählter Name für diese Person (z.B. "tobi",
                 "basti"). Muss bei jedem Aufruf für dieselbe Person identisch sein.
        mood: Die gewünschte Stimmung/das Genre für die Playlist. Funktioniert am besten
              mit kurzen, gängigen englischen Begriffen, die auch als Spotify-Suchbegriff
              Sinn ergeben, z.B. "chill", "energetic", "sad", "focus", "party", "workout",
              "melancholic", "upbeat". Leite den passendsten Begriff aus dem Gesprächskontext
              ab, auch wenn der Nutzer es anders formuliert (z.B. "mir ist nach Runterkommen"
              → mood="chill").
        description: Eine kurze, für Menschen lesbare Beschreibung der Playlist (1 Satz),
                     die du selbst aus dem Gesprächskontext formulierst - nicht einfach
                     den mood-Wert wiederholen. Z.B. "Ruhige Songs zum Entspannen nach
                     einem stressigen Tag."

    Returns:
        Eine Bestätigungsnachricht, oder ein Hinweis falls der Nutzer sich erst noch
        mit Spotify verbinden muss.
    """
    access_token = None
    
    tokens = get_tokens(user_id)
    if tokens is None:
        return "Nutzer hat Claude nicht mit Spotify verbunden."
    
    if tokens["expires_at"] < time.time():
        new_tokens = refresh_access_token(tokens["refresh_token"])
        save_tokens(user_id, new_tokens["access_token"], new_tokens["refresh_token"], new_tokens["expires_at"])
        access_token = new_tokens["access_token"]
    else:
        access_token = tokens["access_token"]
    
    spotify_client = get_spotify_client(access_token)
    track_uris = search_tracks_by_mood(spotify_client, mood)
    playlist_id = create_playlist(spotify_client, f"Claude-{mood}", description)
    add_tracks_to_playlist(spotify_client, playlist_id, track_uris)
    
    return f'Neue Playlist "Claude-{mood}" erstellt mit {len(track_uris)} Songs.'


app.mount("/", mcp.streamable_http_app())