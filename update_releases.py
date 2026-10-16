import os
import json
import requests
import sys

# Sleutels ophalen en automatisch haakjes/spaties verwijderen
client_id = os.environ.get('SPOTIFY_CLIENT_ID', '').strip('() ')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET', '').strip('() ')

print(f"DEBUG: Client ID lengte = {len(client_id)}, Client Secret lengte = {len(client_secret)}")

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

def fetch_new_trance_releases():
    token = get_spotify_token()
    if not token:
        sys.exit(1) # Laat de action rood worden als auth mislukt!

    headers = {'Authorization': f'Bearer {token}'}
    
    params = {
        'q': 'trance',
        'type': 'track',
        'limit': 20
    }
    res = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    
    if res.status_code != 200:
        print(f"❌ SEARCH FOUT [{res.status_code}]: {res.text}")
        sys.exit(1)

    data = res.json()
    tracks = data.get('tracks', {}).get('items', [])
    print(f"✅ Gevonden nummers bij Spotify: {len(tracks)}")

    releases = []
    seen = set()

    for item in tracks:
        track_name = item.get('name', '')
        artists_list = [a['name'] for a in item.get('artists', [])]
        artists = ", ".join(artists_list)
        key = f"{track_name.lower()}_{artists.lower()}"

        if key in seen:
            continue
        seen.add(key)

        album = item.get('album', {})
        images = album.get('images', [])
        img_url = images[0]['url'] if images else 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'
        album_name = album.get('name', 'Trance Release')

        source = 'beatport'
        artist_lower = artists.lower()
        album_lower = album_name.lower()

        if any(k in artist_lower or k in album_lower for k in ['armin', 'armada', 'armind']):
            source = 'armada'
        elif any(k in artist_lower or k in album_lower for k in ['above', 'anjuna']):
            source = 'anjuna'
        elif any(k in artist_lower or k in album_lower for k in ['aly', 'fsoe', 'egypt']):
            source = 'fsoe'
        elif any(k in artist_lower or k in album_lower for k in ['black hole', 'solarstone', 'tiesto']):
            source = 'blackhole'

        releases.append({
            "id": f"rel_{len(releases)+1}",
            "title": track_name,
            "artist": artists,
            "label": album_name,
            "source": source,
            "tag": "Release Friday",
            "image": img_url
        })

        if len(releases) >= 12:
            break

    return releases

if __name__ == '__main__':
    new_releases = fetch_new_trance_releases()
    if new_releases:
        with open('releases.json', 'w', encoding='utf-8') as f:
            json.dump(new_releases, f, ensure_ascii=False, indent=2)
        print(f"🎉 Succesvol {len(new_releases)} nieuwe releases opgeslagen in releases.json!")
    else:
        print("❌ Geen nummers gevonden.")
        sys.exit(1)
