from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from auth import get_auth_url, exchange_code_for_tokens
from db import init_db, save_tokens, get_tokens

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from contextlib import asynccontextmanager

from spotify_client import get_spotify_client, search_tracks_by_queries, create_playlist, add_tracks_to_playlist
from auth import refresh_access_token

import time

mcp = FastMCP(
    "spotify-mood",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["spotify-mood-mcp.onrender.com"]
    )
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield
        
app = FastAPI(lifespan=lifespan)

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
def create_mood_playlist(user_id: str, queries: list[str], description: str, playlist_name: str) -> str:
    """
    Erstellt eine neue Spotify-Playlist für einen bestimmten Nutzer, passend zu seinem Wunsch.

    WICHTIG - user_id ermitteln:
    Falls du für diese Person noch keinen gespeicherten Namen/user_id kennst
    (z.B. aus dem bisherigen Gesprächsverlauf oder deinem Gedächtnis), frag sie
    einmalig: "Wie soll ich dich intern nennen, damit ich deine Spotify-Verbindung
    wiedererkenne?" und merke dir die Antwort für zukünftige Gespräche mit dieser Person.
    Nutze exakt diesen Namen als user_id bei jedem weiteren Aufruf dieses Tools.

    Falls die Funktion zurückgibt, dass der Nutzer nicht verbunden ist: du MUSST eine
    echte, funktionierende URL ausgeben, indem du user_id in folgendem Muster ersetzt:

    https://spotify-mood-mcp.onrender.com/login/USER_ID_HIER

    Beispiel: bei user_id="tobi" gibst du exakt aus:
    https://spotify-mood-mcp.onrender.com/login/tobi

    NIEMALS "<server-url>", "<user_id>" oder ähnliche Platzhalter in Spitzklammern
    wörtlich in deiner Antwort ausgeben - das sind nur Beschreibungen für dich, keine
    Texte die der Nutzer sehen soll. Nutze immer https (nicht http) und genau die
    Domain spotify-mood-mcp.onrender.com. Der Nutzer soll ausschließlich auf einen
    fertigen, klickbaren Link treffen, den er ohne jede eigene Anpassung anklicken kann.

    WICHTIG - queries selbst formulieren:
    Überlege dir konkrete, dir bekannte Songs (Titel + Künstler), die zur Anfrage passen -
    keine abstrakten Genre- oder Stimmungswörter. Formuliere jede Query als "<Songtitel>
    <Künstlername>", z.B. "Rumble Skrillex Fred again", "The Search NF". Wenn ein bestimmter
    Künstler genannt wurde, wähle mehrere unterschiedliche bekannte Songs von genau diesem
    Künstler. Wenn kein Künstler genannt wurde, überlege dir Songs verschiedener Künstler,
    die zur gewünschten Stimmung/zum Anlass passen. Baue 5-8 Queries für eine abwechslungsreiche
    Playlist. Beispiel: Nutzer will "Sport-Playlist mit NEFFEX-Songs" ->
    queries=["Fight Back NEFFEX", "Rumors NEFFEX", "Rebel NEFFEX", "Rockstar NEFFEX",
    "Rage NEFFEX", "Rise NEFFEX"].

    Args:
        user_id: Ein eindeutiger, selbstgewählter Name für diese Person (z.B. "tobi",
                 "basti"). Muss bei jedem Aufruf für dieselbe Person identisch sein.
        queries: Liste von 5-8 Suchbegriffen im Format "<Songtitel> <Künstler>", die konkrete,
                 dir bekannte Songs beschreiben (siehe Hinweis oben) - keine Genre- oder
                 Stimmungswörter. Jede Query wird einzeln durchsucht, die Ergebnisse werden zu
                 einer Playlist zusammengeführt.
        description: Eine kurze, für Menschen lesbare Beschreibung der Playlist (1 Satz),
                     die du selbst aus dem Gesprächskontext formulierst. Z.B. "Energiegeladene
                     NEFFEX-Songs fürs Workout."
        playlist_name: Ein passender, kurzer Name für die Playlist, den du selbst aus dem
                      Gesprächskontext ableitest (z.B. "Workout Motivation", "Chill Vibes").

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
    track_uris = search_tracks_by_queries(spotify_client, queries)
    playlist_id = create_playlist(spotify_client, playlist_name, description)
    add_tracks_to_playlist(spotify_client, playlist_id, track_uris)
    
    return f'Neue Playlist "{playlist_name}" erstellt mit {len(track_uris)} Songs.'


app.mount("/", mcp.streamable_http_app())