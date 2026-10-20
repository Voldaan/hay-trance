import os
import json
import requests

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

PLAYLISTS = [
    {"id": "4tFwX1cGjtcEEaw553hUiK", "label": "Coldharbour", "source": "beatport"},
    {"id": "1y7pBdORcCwCO1yTs6rOM7", "label": "Subculture", "source": "fsoe"},
    {"id": "1RX2XgpOYPAHPptQZZq5aF", "label": "ASOT / Armada", "source": "armada"},
    {"id": "6z1ttXViMg0vODCypY6Snh", "label": "Black Hole", "source": "blackhole"},
    {"id": "4xuIYKnKDLb3bzUIM0uNnM", "label": "FSOE", "source": "fsoe"},
    {"id": "2iTMQ36cvjhxgIYGv7uld5", "label": "Armada Music", "source": "armada"},
    {"id": "2BfXSgtwWVSoHwVhaiv8B1", "label": "In Trance We Trust", "source": "blackhole"},
    {"id": "4qKRxGCBWBKQjXpB2TXhP2", "label": "Anjunabeats", "source": "anjuna"}
]

def get_spotify_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ FOUT: SPOTIFY_CLIENT_ID of SPOTIFY_CLIENT_SECRET is niet ingesteld in GitHub Secrets!")
        return None

    auth_url = "https://accounts.spotify.com/api/token"
    response = requests.post(
        auth_url,
        data={'grant_type': 'client_credentials'},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    
    if response.status_code != 200:
        print(f"❌ FOUT bij ophalen Spotify token (Status {response.status_code}): {response.text}")
        return None

    return response.json().get('access_token')

def fetch_playlist_tracks(token, playlist_id, source, label):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=12"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        print(f"⚠️ Playlist ID {playlist_id} kon niet opgevraagd worden (Status {res.status_code})")
        return []

    tracks_data = []
    items = res.json().get('items', [])
    for idx, item in enumerate(items):
        track = item.get('track')
        if track and track.get('name'):
            title = track['name']
            artists = ", ".join([a['name'] for a in track['artists']])
            images = track.get('album', {}).get('images', [])
            img_url = images[0]['url'] if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"
            
            tracks_data.append({
                "id": f"{playlist_id}_{idx}",
                "title": title,
                "artist": artists,
                "label": label,
                "image": img_url,
                "source": source,
                "tag": "Release"
            })
    return tracks_data

def main():
    token = get_spotify_token()
    if not token:
        print("❌ Kan de workflow niet voortzetten zonder een geldig Spotify Token.")
        exit(1)

    all_releases = []
    seen_keys = set()

    for pl in PLAYLISTS:
        tracks = fetch_playlist_tracks(token, pl['id'], pl['source'], pl['label'])
        for t in tracks:
            key = f"{t['title'].lower()}_{t['artist'].lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                all_releases.append(t)

    if not all_releases:
        print("❌ Geen nummers gevonden.")
        exit(1)

    with open("releases.json", "w", encoding="utf-8") as f:
        json.dump(all_releases, f, ensure_ascii=False, indent=2)

    print(f"✅ Succesvol {len(all_releases)} geselecteerde trance-tracks verwerkt uit alle 8 afspeellijsten!")

if __name__ == "__main__":
    main()
