# CLI Music Player

A command-line music player built with Python and VLC.

## Requirements

- Python 3.x
- [python-vlc](https://pypi.org/project/python-vlc/)
- VLC media player installed on your system

## Installation

```bash
pip install python-vlc
```

## Usage

```bash
python main.py <path-to-music-directory>
```

**Example:**
```bash
python main.py ./music
```

## Commands

| Command | Description |
|---|---|
| `play` | Play the queue (loads all songs from the directory if empty) |
| `play <filename>` | Stop current song and play a specific song immediately |
| `pause` | Pause or resume playback |
| `stop` | Stop playback |
| `skip` | Skip to the next song |
| `shuffle` | Shuffle the queue and start playing |
| `add <filename>` | Add a specific song to the queue |
| `volume <0-100>` | Set the volume |
| `search <query>` | Search for songs in the directory matching the query |
| `list` | Show the current queue |
| `empty` | Clear the queue |
| `clear` | Clear the terminal screen |
| `quit` / `exit` | Exit the player |
| `playlist create <name>` | Create a new playlist |
| `playlist add <name> <filename>` | Add a song to a playlist |
| `playlist play <name>` | Play a playlist |
| `playlist list` | List all playlists |
| `playlist delete <name>` | Delete a playlist |

## Supported Formats

`.mp3`, `.wav`, `.ogg`, `.flac`
