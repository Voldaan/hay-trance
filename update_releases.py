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

def fetch_pure_trance_releases():
    token = get_spotify_token()
    if not token:
        sys.exit(1)

    headers = {'Authorization': f'Bearer {token}'}

    # 100% Geverifieerde Trance-labels
    trance_labels = [
        {"name": "Armada Music", "source": "armada", "tag": "Armada"},
        {"name": "Anjunabeats", "source": "anjuna", "tag": "Anjunabeats"},
        {"name": "Black Hole Recordings", "source": "blackhole", "tag": "Black Hole"},
        {"name": "Future Sound of Egypt", "source": "fsoe", "tag": "FSOE"},
        {"name": "VANDIT Records", "source": "beatport", "tag": "VANDIT"},
        {"name": "Flashover Recordings", "source": "beatport", "tag": "Flashover"},
        {"name": "Coldharbour Recordings", "source": "beatport", "tag": "Coldharbour"},
        {"name": "Subculture", "source": "fsoe", "tag": "Subculture"},
        {"name": "Who's Afraid Of 138?!", "source": "armada", "tag": "WAO138?!"},
        {"name": "In Trance We Trust", "source": "blackhole", "tag": "ITWT"}
    ]

    all_releases = []
    seen = set()

    for label_info in trance_labels:
        label_name = label_info["name"]
        
        # Zoek direct op het officiële platenlabel bij Spotify
        params = {
            'q': f'label:"{label_name}"',
            'type': 'album',
            'limit': 5
        }
        res = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
        
        if res.status_code != 200:
            continue

        data = res.json()
        albums = data.get('albums', {}).get('items', [])

        for album in albums:
            release_date = album.get('release_date', '')
            album_name = album.get('name', '')
            artists_list = [a['name'] for a in album.get('artists', [])]
            artists = ", ".join(artists_list)
            images = album.get('images', [])
            img_url = images[0]['url'] if images else 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'

            key = f"{album_name.lower()}_{artists.lower()}"
            if key in seen:
                continue
            seen.add(key)

            all_releases.append({
                "id": f"rel_{len(all_releases)+1}",
                "title": album_name,
                "artist": artists,
                "label": label_name,
                "source": label_info["source"],
                "tag": label_info["tag"],
                "image": img_url,
                "release_date": release_date
            })

    # Sorteer alle gevonden platen op meest recente releasedatum
    all_releases.sort(key=lambda x: x.get('release_date', ''), reverse=True)

    # Pak de top 12 allernieuwste geverifieerde trance-releases
    final_releases = all_releases[:12]
    
    for idx, item in enumerate(final_releases):
        item["id"] = f"rel_{idx+1}"

    print(f"✅ Gevonden geverifieerde trance releases: {len(final_releases)}")
    return final_releases

if __name__ == '__main__':
    new_releases = fetch_pure_trance_releases()
    if new_releases:
        with open('releases.json', 'w', encoding='utf-8') as f:
            json.dump(new_releases, f, ensure_ascii=False, indent=2)
        print(f"🎉 Succesvol {len(new_releases)} pure trance releases opgeslagen in releases.json!")
    else:
        print("❌ Geen releases gevonden.")
        sys.exit(1)
