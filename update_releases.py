import os
import json
import requests

# Sleutels ophalen uit GitHub Secrets
client_id = os.environ.get('SPOTIFY_CLIENT_ID')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')

def get_spotify_token():
    auth_response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    return auth_response.json().get('access_token')

def fetch_new_trance_releases():
    token = get_spotify_token()
    if not token:
        print("Kan geen toegangstoken ophalen bij Spotify.")
        return []

    headers = {'Authorization': f'Bearer {token}'}
    
    # Zoek de nieuwste releases in het genre Trance
    params = {
        'q': 'genre:trance tag:new',
        'type': 'track',
        'limit': 12
    }
    
    res = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    data = res.json()

    releases = []
    tracks = data.get('tracks', {}).get('items', [])

    for idx, item in enumerate(tracks):
        album = item.get('album', {})
        images = album.get('images', [])
        img_url = images[0]['url'] if images else 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'
        artists = ", ".join([a['name'] for a in item.get('artists', [])])
        
        title = item.get('name', '')
        album_name = album.get('name', 'Trance Release')

        # Bepaal categorie
        source = 'all'
        artist_lower = artists.lower()
        if 'armin' in artist_lower or 'armada' in album_name.lower():
            source = 'armada'
        elif 'above' in artist_lower or 'anjuna' in album_name.lower():
            source = 'anjuna'
        elif 'aly' in artist_lower or 'fsoe' in album_name.lower():
            source = 'fsoe'

        releases.append({
            "id": f"rel_{idx+1}",
            "title": title,
            "artist": artists,
            "label": album_name,
            "source": source,
            "tag": "Release Friday",
            "image": img_url
        })

    return releases

if __name__ == '__main__':
    new_releases = fetch_new_trance_releases()
    if new_releases:
        with open('releases.json', 'w', encoding='utf-8') as f:
            json.dump(new_releases, f, ensure_ascii=False, indent=2)
        print(f"Succesvol {len(new_releases)} nieuwe releases opgeslagen in releases.json!")
