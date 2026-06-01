import time
import threading
import os
import random
from collections import deque
import vlc
from rich.console import Console

console = Console()


class MusicPlayer:
    def __init__(self, music_dir):
        self.music_dir = music_dir
        self.current_song = None
        self.play_thread = None
        self.instance = vlc.Instance("--quiet")
        self.player = self.instance.media_player_new()
        self.volume = 100
        self.is_playing = False
        self.is_paused = False
        self.play_thread = None
        self.queue = deque()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def _get_song_path(self, song_name):
        path = os.path.join(self.music_dir, song_name)
        if not os.path.isfile(path):
            for filename in os.listdir(self.music_dir):
                if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) and song_name.lower() in filename.lower():
                    return os.path.join(self.music_dir, filename)
            raise FileNotFoundError(f"song not found: {song_name}")
        return path
    
    def search_song(self, query):
        matches = []
        for filename in os.listdir(self.music_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) and query.lower() in filename.lower():
                matches.append(filename)
        return matches

    def add_to_queue(self, song_path):
        song_path = self._get_song_path(song_path)
        if not os.path.exists(song_path):
            console.print("[red]Song not found.[/red]")
            return
        self.queue.append(song_path)
        console.print(f"[green]Added[/green] {os.path.basename(song_path)} to queue.")

    def shuffle(self):
        with self.lock:
            if not self.queue:
                self.add_all_songs()

            shuffled = list(self.queue)
            random.shuffle(shuffled)
            self.queue = deque(shuffled)
            console.print("[cyan]Queue shuffled.[/cyan]")

            if not self.is_playing:
                self.is_playing = True
                self._play_next()

    def skip(self):
        if not self.is_playing:
            console.print("[yellow]There is nothing to skip.[/yellow]")
            return
        self.stop_event.set()

        if self.player:
            self.player.stop()

        self.stop_event.clear()
        self.is_paused = False

        self._play_next()

    def add_all_songs(self):
        added = 0
        for filename in os.listdir(self.music_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                full_path = os.path.join(self.music_dir, filename)
                self.queue.append(full_path)
                added += 1
        console.print(f"[green]Added {added} songs[/green] from {self.music_dir} to the queue.")

    def clear_queue(self):
        cleared = len(self.queue)
        self.queue.clear()
        console.print(f"[yellow]Cleared {cleared} songs from the queue.[/yellow]")

    def list_queue(self):
        if not self.queue:
            print("queue is empty.")
            return
        print("Queue:")
        for i, song in enumerate(self.queue, 1):
            print(f"{i}. {os.path.basename(song)}")

    def _on_song_end(self, event):
        if self.stop_event.is_set():
            return
        time.sleep(0.1)
        self._play_next()

    def _play_next(self):
        if not self.queue or self.stop_event.is_set():
            self.is_playing = False
            console.print("[yellow]Queue finished.[/yellow]")
            return

        song = self.queue.popleft()
        console.print(f"[bold green]Now Playing:[/bold green] {os.path.basename(song)}")

        self.player = self.instance.media_player_new()
        media = self.instance.media_new(song)
        self.player.set_media(media)

        self.player.audio_set_volume(self.volume)

        events = self.player.event_manager()
        events.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_song_end
        )
        self.player.play()

    def play(self, song=None):
        if song:
            song_path = self._get_song_path(song)
            if self.player:
                self.player.stop()
            self.stop_event.clear()
            self.is_paused = False
            self.is_playing = True
            self.player = self.instance.media_player_new()
            media = self.instance.media_new(song_path)
            self.player.set_media(media)
            self.player.audio_set_volume(self.volume)
            events = self.player.event_manager()
            events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_song_end)
            self.player.play()
            console.print(f"[bold green]Now Playing:[/bold green] {song}")
            return

        if self.is_playing and self.is_paused:
            self.player.play()
            self.is_paused = False
            console.print("[green]Resumed.[/green]")
            return

        if self.is_playing:
            return

        self.stop_event.clear()

        if not self.queue:
            self.add_all_songs()

        if not self.queue:
            console.print("[yellow]No songs to play.[/yellow]")
            return

        self.is_playing = True
        self._play_next()

    def pause(self):
        if not self.is_playing:
            console.print("[yellow]Nothing is playing.[/yellow]")
            return

        if self.is_paused:
            self.player.play()
            self.is_paused = False
            console.print("[green]Resumed.[/green]")
        else:
            self.player.pause()
            self.is_paused = True
            console.print("[yellow]Paused.[/yellow]")

    def stop(self):
        with self.lock:
            if self.player:
                self.player.stop()
            self.paused = False
            self.stop_event.set()
            console.print("[red]Playback stopped.[/red]")

    def set_volume(self, volume):
        if not 0 <= volume <= 100:
            console.print("[red]Volume must be between 0 and 100.[/red]")
            return
        with self.lock:
            self.volume = volume
            if self.player:
                self.player.audio_set_volume(volume)
        console.print(f"[green]Volume set to {volume}.[/green]")
