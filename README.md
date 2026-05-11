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
| `pause` | Pause or resume playback |
| `stop` | Stop playback |
| `skip` | Skip to the next song |
| `shuffle` | Shuffle the queue and start playing |
| `add <filename>` | Add a specific song to the queue |
| `volume <0-100>` | Set the volume |
| `list` | Show the current queue |
| `clear` | Clear the terminal screen |
| `quit` / `exit` | Exit the player |

## Supported Formats

`.mp3`, `.wav`, `.ogg`, `.flac`
