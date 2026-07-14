from dotenv import load_dotenv
from urllib.parse import urlencode
import requests
import time
import os

load_dotenv()

def get_auth_url(user_id: str) -> str:
    spotify_authorize_url = "https://accounts.spotify.com/authorize"
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "playlist-modify-public playlist-modify-private",
        "state": user_id
    }
    
    query_string = urlencode(params)
    full_url = spotify_authorize_url + "?" + query_string
    
    return full_url


def exchange_code_for_tokens(code: str) -> dict:
    spotify_token_url = "https://accounts.spotify.com/api/token"
    
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    form_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(spotify_token_url, data=form_data)
    
    data = response.json()
    
    expires_in = data["expires_in"]
    expires_at = time.time() + expires_in
    data["expires_at"] = expires_at
    
    return data


def refresh_access_token(refresh_token: str) -> dict:
    spotify_token_url = "https://accounts.spotify.com/api/token"
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    form_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(spotify_token_url, data=form_data)
    
    data = response.json()
    
    expires_in = data["expires_in"]
    expires_at = time.time() + expires_in
    data["expires_at"] = expires_at
    
    data["refresh_token"] = data.get("refresh_token", refresh_token)
    
    return data