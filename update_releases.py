import os
import json
import re
import requests

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# De 8 afspeellijsten
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

def get_spotify_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    auth_url = "https://accounts.spotify.com/api/token"
    try:
        response = requests.post(
            auth_url,
            data={'grant_type': 'client_credentials'},
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception as e:
        print(f"⚠️ Token ophalen mislukt: {e}")
    return None

def fetch_via_api(token, playlist_id, source, label):
    """Probeer nummers via de officiële Spotify API op te halen"""
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=12"
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers, timeout=10)
    
    if res.status_code != 200:
        return None

    tracks_data = []
    items = res.json().get('items', [])
    for idx, item in enumerate(items):
        track = item.get('track')
        if track and track.get('name'):
            title = track['name']
            artists = ", ".join([a['name'] for a in track['artists']])
            images = track.get('album', {}).get('images', [])
            img_url = images[0]['url'] if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"
            release_date = track.get('album', {}).get('release_date', '')
            
            tracks_data.append({
                "id": f"rel_{playlist_id[:6]}_{idx}",
                "title": title,
                "artist": artists,
                "label": label,
                "source": source,
                "tag": label,
                "image": img_url,
                "release_date": release_date
            })
    return tracks_data

def fetch_via_embed_scrape(playlist_id, source, label):
    """Fallback: Haal afspeellijst data op via de publieke Spotify Embed player"""
    url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    
    if res.status_code != 200:
        print(f"❌ Embed ophalen mislukt voor playlist {playlist_id} (Status {res.status_code})")
        return []

    tracks_data = []
    try:
        # Zoek JSON data in de embed HTML
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
        if match:
            json_data = json.loads(match.group(1))
            entity = json_data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
            track_list = entity.get('trackList', [])

            for idx, item in enumerate(track_list[:12]):
                title = item.get('title', '')
                artists = item.get('subtitle', '')
                img_url = item.get('coverArt', {}).get('sources', [{}])[0].get('url', 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400')
                
                if title:
                    tracks_data.append({
                        "id": f"rel_{playlist_id[:6]}_{idx}",
                        "title": title,
                        "artist": artists,
                        "label": label,
                        "source": source,
                        "tag": label,
                        "image": img_url,
                        "release_date": ""
                    })
    except Exception as e:
        print(f"⚠️ Fout bij verwerken embed HTML voor {playlist_id}: {e}")

    return tracks_data

def main():
    token = get_spotify_token()
    all_releases = []
    seen_keys = set()

    for pl in PLAYLISTS:
        tracks = None
        # Stap 1: Probeer via API (als token aanwezig is)
        if token:
            tracks = fetch_via_api(token, pl['id'], pl['source'], pl['label'])
        
        # Stap 2: Gebruik Embed scraping als API faalt of 403 geeft
        if not tracks:
            tracks = fetch_via_embed_scrape(pl['id'], pl['source'], pl['label'])

        if tracks:
            print(f"✅ {len(tracks)} nummers opgehaald voor {pl['label']}")
            for t in tracks:
                key = f"{t['title'].lower()}_{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_releases.append(t)
        else:
            print(f"⚠️ Geen nummers kunnen vinden voor {pl['label']}")

    if not all_releases:
        print("❌ Geen enkele nummer kunnen ophalen uit alle afspeellijsten.")
        exit(1)

    # Bewaar in releases.json
    with open("releases.json", "w", encoding="utf-8") as f:
        json.dump(all_releases, f, ensure_ascii=False, indent=2)

    print(f"🎉 Succesvol {len(all_releases)} unieke trance-releases opgeslagen in releases.json!")

if __name__ == "__main__":
    main()
