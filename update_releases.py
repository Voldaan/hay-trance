import os
import json
import requests
import sys

# Sleutels ophalen uit GitHub Secrets
client_id = os.environ.get('SPOTIFY_CLIENT_ID', '').strip('() ')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET', '').strip('() ')

def get_spotify_token():
    auth_response = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    if auth_response.status_code == 200:
        return auth_response.json().get('access_token')
    
    print(f"❌ SPOTIFY AUTH FOUT [{auth_response.status_code}]: {auth_response.text}")
    return None

def fetch_releases_from_curated_playlists():
    token = get_spotify_token()
    if not token:
        sys.exit(1)

    headers = {'Authorization': f'Bearer {token}'}

    # Alle 8 unieke top-playlists van Spotify
    playlists = [
        {"id": "4tFwX1cGjtcEEaw553hUiK", "source": "beatport", "tag": "Coldharbour"},
        {"id": "1y7pBdORcCwCO1yTs6rOM7", "source": "fsoe", "tag": "Subculture"},
        {"id": "1RX2XgpOYPAHPptQZZq5aF", "source": "armada", "tag": "ASOT 2026"},
        {"id": "6z1ttXViMg0vODCypY6Snh", "source": "blackhole", "tag": "Black Hole"},
        {"id": "4xuIYKnKDLb3bzUIM0uNnM", "source": "fsoe", "tag": "FSOE"},
        {"id": "2iTMQ36cvjhxgIYGv7uld5", "source": "armada", "tag": "Armada Music"},
        {"id": "2BfXSgtwWVSoHwVhaiv8B1", "source": "blackhole", "tag": "ITWT"},
        {"id": "4qKRxGCBWBKQjXpB2TXhP2", "source": "anjuna", "tag": "Anjunabeats"}
    ]

    all_tracks = []
    seen = set()

    for pl in playlists:
        pid = pl["id"]
        url = f'https://api.spotify.com/v1/playlists/{pid}/tracks?limit=15'
        
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"⚠️ Playlist ID {pid} kon niet opgevraagd worden (Status {res.status_code})")
            continue

        data = res.json()
        items = data.get('items', [])

        for item in items:
            track = item.get('track')
            if not track:
                continue

            track_name = track.get('name', '')
            artists_list = [a['name'] for a in track.get('artists', [])]
            artists = ", ".join(artists_list)
            
            key = f"{track_name.lower()}_{artists.lower()}"
            if key in seen:
                continue
            seen.add(key)

            album = track.get('album', {})
            images = album.get('images', [])
            img_url = images[0]['url'] if images else 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'
            album_name = album.get('name', 'Trance Release')
            release_date = album.get('release_date', '')

            all_tracks.append({
                "title": track_name,
                "artist": artists,
                "label": album_name,
                "source": pl["source"],
                "tag": pl["tag"],
                "image": img_url,
                "release_date": release_date
            })

    # Sorteer op meest recente releasedatum (nieuwste eerst)
    all_tracks.sort(key=lambda x: x.get('release_date', ''), reverse=True)

    # Pak de top 12 allernieuwste en beste nummers
    final_releases = all_tracks[:12]
    for idx, item in enumerate(final_releases):
        item["id"] = f"rel_{idx+1}"

    print(f"✅ Succesvol {len(final_releases)} geselecteerde trance-tracks verwerkt uit alle 8 afspeellijsten!")
    return final_releases

if __name__ == '__main__':
    new_releases = fetch_releases_from_curated_playlists()
    if new_releases:
        with open('releases.json', 'w', encoding='utf-8') as f:
            json.dump(new_releases, f, ensure_ascii=False, indent=2)
        print("🎉 releases.json is succesvol bijgewerkt met jouw 8 gekozen afspeellijsten!")
    else:
        print("❌ Geen nummers gevonden.")
        sys.exit(1)
