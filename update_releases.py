import os
import json
import requests
import sys
from datetime import datetime, timedelta

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

    # Zoekopdrachten per officieel trance-label
    queries = [
        {"q": 'label:"Coldharbour Recordings"', "source": "beatport", "tag": "Coldharbour"},
        {"q": 'label:"Subculture"', "source": "fsoe", "tag": "Subculture"},
        {"q": 'label:"A State Of Trance"', "source": "armada", "tag": "ASOT"},
        {"q": 'label:"Black Hole Recordings"', "source": "blackhole", "tag": "Black Hole"},
        {"q": 'label:"Future Sound Of Egypt"', "source": "fsoe", "tag": "FSOE"},
        {"q": 'label:"Armada Music"', "source": "armada", "tag": "Armada"},
        {"q": 'label:"In Trance We Trust"', "source": "blackhole", "tag": "ITWT"},
        {"q": 'label:"Anjunabeats"', "source": "anjuna", "tag": "Anjunabeats"}
    ]

    # Dynamische datumfilter: uitsluitend nummers uit de afgelopen 7 dagen
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    all_tracks = []
    seen = set()

    for item_q in queries:
        params = {
            'q': item_q["q"],
            'type': 'track',
            'limit': 20  # Ruim opvragen om alle platen van de afgelopen week mee te pakken
        }
        res = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
        
        if res.status_code != 200:
            print(f"⚠️ Zoekopdracht {item_q['q']} mislukt (Status {res.status_code})")
            continue

        data = res.json()
        tracks = data.get('tracks', {}).get('items', [])

        for track in tracks:
            track_name = track.get('name', '')
            artists_list = [a['name'] for a in track.get('artists', [])]
            artists = ", ".join(artists_list)
            
            key = f"{track_name.lower()}_{artists.lower()}"
            if key in seen:
                continue

            album = track.get('album', {})
            release_date = album.get('release_date', '')

            # Filter op versheid: streng negeren wat ouder is dan 7 dagen
            if release_date and release_date < cutoff_date:
                continue

            seen.add(key)

            images = album.get('images', [])
            img_url = images[0]['url'] if images else 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'
            album_name = album.get('name', 'Trance Release')

            all_tracks.append({
                "title": track_name,
                "artist": artists,
                "label": album_name,
                "source": item_q["source"],
                "tag": item_q["tag"],
                "image": img_url,
                "release_date": release_date
            })

    # Sorteer op meest recente releasedatum (nieuwste eerst)
    all_tracks.sort(key=lambda x: x.get('release_date', ''), reverse=True)

    # Bewaar een royale pool (tot 80 nummers van de afgelopen 7 dagen)
    final_releases = all_tracks[:80]
    for idx, item in enumerate(final_releases):
        item["id"] = f"rel_{idx+1}"

    print(f"✅ Succesvol {len(final_releases)} verse trance-tracks (afgelopen 7 dagen) opgeslagen!")
    return final_releases

if __name__ == '__main__':
    new_releases = fetch_pure_trance_releases()
    if new_releases:
        with open('releases.json', 'w', encoding='utf-8') as f:
            json.dump(new_releases, f, ensure_ascii=False, indent=2)
        print("🎉 releases.json is succesvol bijgewerkt met 7-dagen releases!")
    else:
        print("❌ Geen nummers gevonden.")
        sys.exit(1)
