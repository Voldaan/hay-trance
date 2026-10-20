import os
import json
import re
import urllib.parse
import requests

# De 8 Spotify afspeellijsten met hun labels en bronnen
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

def get_track_image(track_id, artist, title):
    """
    Haalt de specifieke albumhoes op per nummer.
    1. Via Spotify Track oEmbed API (op basis van track_id)
    2. Via iTunes Search API (fallback voor 600x600 HD artwork)
    """
    # 1. Probeer Spotify Track oEmbed
    if track_id:
        try:
            oembed_url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}"
            res = requests.get(oembed_url, headers=HEADERS, timeout=5)
            if res.status_code == 200:
                thumb = res.json().get('thumbnail_url')
                if thumb and ('scdn.co' in thumb or 'spotifycdn.com' in thumb):
                    return thumb
        except Exception as e:
            print(f"⚠️ Spotify track oEmbed mislukt voor {track_id}: {e}")

    # 2. Fallback via iTunes Search API (100% gratis, publiek en zeer nauwkeurig)
    try:
        query = urllib.parse.quote(f"{artist} {title}")
        itunes_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        res = requests.get(itunes_url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            results = res.json().get('results', [])
            if results and 'artworkUrl100' in results[0]:
                return results[0]['artworkUrl100'].replace('100x100bb', '600x600bb')
    except Exception as e:
        print(f"⚠️ iTunes fallback mislukt voor {artist} - {title}: {e}")

    return "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"

def fetch_playlist_tracks(playlist_id, source, label):
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    tracks_data = []

    try:
        res = requests.get(embed_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"❌ Embed ophalen mislukt voor {label} (Status {res.status_code})")
            return []

        html = res.text
        match = re.search(r'<script id="(?:__NEXT_DATA__|session|initial-state)" type="application/json">(.*?)</script>', html)
        
        if match:
            data = json.loads(match.group(1))
            entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
            track_list = entity.get('trackList', [])
            
            for idx, item in enumerate(track_list[:15]):
                title = item.get('title', '').strip()
                artist = item.get('subtitle', '').strip() or item.get('artist', '').strip()
                uri = item.get('uri', '') or item.get('trackUri', '')
                
                # Extraheer Spotify Track ID uit de URI
                track_id = ""
                if "spotify:track:" in uri:
                    track_id = uri.split("spotify:track:")[1].split("?")[0]
                elif "track/" in uri:
                    track_id = uri.split("track/")[1].split("?")[0]

                if title:
                    img_url = get_track_image(track_id, artist, title)
                    tracks_data.append({
                        "id": f"rel_{playlist_id[:5]}_{idx}",
                        "title": title,
                        "artist": artist or "Trance Artist",
                        "label": label,
                        "source": source,
                        "tag": label,
                        "image": img_url
                    })
    except Exception as e:
        print(f"⚠️ Fout bij verwerken {label}: {e}")

    return tracks_data

def main():
    all_releases = []
    seen_keys = set()

    for pl in PLAYLISTS:
        tracks = fetch_playlist_tracks(pl['id'], pl['source'], pl['label'])

        if tracks:
            print(f"✅ {len(tracks)} nummers met unieke covers geladen voor {pl['label']}")
            for t in tracks:
                key = f"{t['title'].lower()}_{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_releases.append(t)
        else:
            print(f"⚠️ Geen nummers kunnen ophalen voor {pl['label']}")

    if not all_releases:
        print("❌ Geen nummers opgeslagen.")
        exit(1)

    with open("releases.json", "w", encoding="utf-8") as f:
        json.dump(all_releases, f, ensure_ascii=False, indent=2)

    print(f"🎉 Succesvol {len(all_releases)} unieke trance-releases met eigen albumcovers opgeslagen in releases.json!")

if __name__ == "__main__":
    main()
