import os
import json
import re
import requests

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# De 8 Spotify afspeellijsten
PLAYLISTS = [
    {"id": "4tFwX1cGjtcEEaw553hUiK", "label": "Coldharbour", "source": "coldharbour"},
    {"id": "1y7pBdORcCwCO1yTs6rOM7", "label": "Subculture", "source": "fsoe"},
    {"id": "1RX2XgpOYPAHPptQZZq5aF", "label": "ASOT", "source": "armada"},
    {"id": "6z1ttXViMg0vODCypY6Snh", "label": "Black Hole", "source": "blackhole"},
    {"id": "4xuIYKnKDLb3bzUIM0uNnM", "label": "FSOE", "source": "fsoe"},
    {"id": "2iTMQ36cvjhxgIYGv7uld5", "label": "Armada Music", "source": "armada"},
    {"id": "2BfXSgtwWVSoHwVhaiv8B1", "label": "In Trance We Trust", "source": "blackhole"},
    {"id": "4qKRxGCBWBKQjXpB2TXhP2", "label": "Anjunabeats", "source": "anjuna"}
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

def get_spotify_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    auth_url = "https://accounts.spotify.com/api/token"
    try:
        res = requests.post(
            auth_url,
            data={'grant_type': 'client_credentials'},
            auth=(CLIENT_ID, CLIENT_SECRET),
            headers=HEADERS,
            timeout=10
        )
        if res.status_code == 200:
            return res.json().get('access_token')
    except Exception as e:
        print(f"⚠️ Token error: {e}")
    return None

def fetch_via_api(token, playlist_id, source, label):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market=NL&limit=15"
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    try:
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
                
                tracks_data.append({
                    "id": f"rel_{playlist_id[:5]}_{idx}",
                    "title": title,
                    "artist": artists,
                    "label": label,
                    "source": source,
                    "tag": label,
                    "image": img_url
                })
        return tracks_data
    except Exception as e:
        print(f"⚠️ API fout: {e}")
        return None

def fetch_via_embed(playlist_id, source, label):
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    try:
        res = requests.get(embed_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []

        html = res.text
        tracks_data = []
        imgs = re.findall(r'https://i\.scdn\.co/image/[a-f0-9]{32,40}', html)

        match = re.search(r'<script id="(?:__NEXT_DATA__|session|initial-state)" type="application/json">(.*?)</script>', html)
        if match:
            data = json.loads(match.group(1))
            entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
            track_list = entity.get('trackList', [])
            
            for idx, item in enumerate(track_list[:15]):
                title = item.get('title', '').strip()
                artist = item.get('subtitle', '').strip()
                
                item_str = json.dumps(item)
                item_imgs = re.findall(r'https://i\.scdn\.co/image/[a-f0-9]{32,40}', item_str)
                if item_imgs:
                    img_url = item_imgs[0]
                elif imgs:
                    img_url = imgs[idx % len(imgs)]
                else:
                    img_url = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"

                if title:
                    tracks_data.append({
                        "id": f"rel_{playlist_id[:5]}_{idx}",
                        "title": title,
                        "artist": artist or "Trance Artist",
                        "label": label,
                        "source": source,
                        "tag": label,
                        "image": img_url
                    })
        return tracks_data
    except Exception as e:
        print(f"⚠️ Embed error: {e}")
        return []

def main():
    token = get_spotify_token()
    all_releases = []
    seen_keys = set()

    for pl in PLAYLISTS:
        tracks = fetch_via_api(token, pl['id'], pl['source'], pl['label']) if token else None
        if not tracks:
            tracks = fetch_via_embed(pl['id'], pl['source'], pl['label'])

        if tracks:
            print(f"✅ {len(tracks)} nummers geladen voor {pl['label']}")
            for t in tracks:
                key = f"{t['title'].lower()}_{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_releases.append(t)

    if not all_releases:
        print("❌ Geen nummers opgehaald.")
        exit(1)

    with open("releases.json", "w", encoding="utf-8") as f:
        json.dump(all_releases, f, ensure_ascii=False, indent=2)

    print(f"🎉 Succesvol {len(all_releases)} unieke trance-releases opgeslagen in releases.json!")

if __name__ == "__main__":
    main()
