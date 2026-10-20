import json
import re
import requests

# De 8 Spotify afspeellijsten
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

def fetch_playlist_tracks(playlist_id, source, label):
    """
    Haalt nummers rechtstreeks op uit de publieke Spotify Embed player.
    Geen API key nodig, dus GEEN 403-fouten meer op GitHub!
    """
    tracks_data = []
    
    # Methode 1: HTML Scrape van de Embed Player
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    try:
        res = requests.get(embed_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            html = res.text
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if not match:
                match = re.search(r'<script id="session" type="application/json">(.*?)</script>', html)
                
            if match:
                data = json.loads(match.group(1))
                entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
                track_list = entity.get('trackList', [])
                
                for idx, item in enumerate(track_list[:12]):
                    title = item.get('title', '').strip()
                    artist = item.get('subtitle', '').strip()
                    images = item.get('coverArt', {}).get('sources', [])
                    img_url = images[0]['url'] if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"
                    
                    if title:
                        tracks_data.append({
                            "id": f"rel_{playlist_id[:5]}_{idx}",
                            "title": title,
                            "artist": artist or "Trance Artist",
                            "label": label,
                            "source": source,
                            "tag": label,
                            "image": img_url,
                            "release_date": ""
                        })
    except Exception as e:
        print(f"⚠️ Embed scrape mislukt voor {playlist_id}: {e}")

    # Methode 2: Spotify oEmbed Fallback
    if not tracks_data:
        try:
            oembed_url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/playlist/{playlist_id}"
            res = requests.get(oembed_url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                oembed_json = res.json()
                thumbnail = oembed_json.get('thumbnail_url', 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400')
                embed_html = oembed_json.get('html', '')
                items = re.findall(r'<li[^>]*>(.*?)</li>', embed_html, re.DOTALL)
                
                for idx, item_html in enumerate(items[:12]):
                    clean_text = re.sub(r'<[^>]+>', ' ', item_html).strip()
                    clean_text = re.sub(r'\s+', ' ', clean_text)
                    parts = clean_text.split('•')
                    if len(parts) >= 2:
                        title = parts[0].strip()
                        artist = parts[1].strip()
                    else:
                        title = clean_text
                        artist = label
                        
                    if title:
                        tracks_data.append({
                            "id": f"rel_{playlist_id[:5]}_{idx}",
                            "title": title,
                            "artist": artist,
                            "label": label,
                            "source": source,
                            "tag": label,
                            "image": thumbnail,
                            "release_date": ""
                        })
        except Exception as e:
            print(f"⚠️ oEmbed fallback mislukt voor {playlist_id}: {e}")

    return tracks_data

def main():
    all_releases = []
    seen_keys = set()

    for pl in PLAYLISTS:
        tracks = fetch_playlist_tracks(pl['id'], pl['source'], pl['label'])
        if tracks:
            print(f"✅ {len(tracks)} nummers opgehaald voor {pl['label']}")
            for t in tracks:
                key = f"{t['title'].lower()}_{t['artist'].lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_releases.append(t)
        else:
            print(f"⚠️ Geen nummers kunnen ophalen voor {pl['label']}")

    if not all_releases:
        print("❌ Geen enkele nummer kunnen ophalen uit alle afspeellijsten.")
        exit(1)

    # Oplaan in releases.json
    with open("releases.json", "w", encoding="utf-8") as f:
        json.dump(all_releases, f, ensure_ascii=False, indent=2)

    print(f"🎉 Succesvol {len(all_releases)} unieke trance-releases opgeslagen in releases.json!")

if __name__ == "__main__":
    main()
