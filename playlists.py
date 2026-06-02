import json



def load_playlists():
    try:
        with open('playlists.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_to_playlists(playlists):
    with open('playlists.json', 'w') as f:
        json.dump(playlists, f)



