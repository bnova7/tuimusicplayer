import argparse 
import sys
import time 
import threading 
import os
import random
from collections import deque
import vlc 

class MusicPlayer:
    def __init__(self, music_dir):
        self.music_dir = music_dir
        self.current_song = None
        self.play_thread = None 
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.volume = 100
        self.is_playing = False
        self.is_paused = False
        self.play_thread = None
        self.queue = deque()
        self.lock = threading.Lock()#locks the threads to prevent race condition, we put it here so all the methods have it 
        self.stop_event = threading.Event()
    
    def _get_song_path(self, song_name):
        path = os.path.join(self.music_dir, song_name)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"song not found: {song_name}")
        return path
    
    def add_to_queue(self, song_name):
        song_path = self._get_song_path(song_name)
        if not os.path.exists(song_path):
            print(f"song not found")
            return
        self.queue.append(song_name)
        print(f"Added {song_name} to queue.")

    def clear_screen(self):
        os.system("cls" if os.name == "nt"
                  else "clear")


    def shuffle(self):
        with self.lock:
            if not self.queue:
                self.add_all_songs()

            shuffled = list(self.queue)
            random.shuffle(shuffled)
            self.queue = deque(shuffled)
            print("Queue shuffled")

            if not self.is_playing:
                self._play_next()



    def skip(self):
        if not self.is_playing: #doesnt skip if nothing is playing
            print("There is nothing to skip.")
            return
        self.stop_event.set() #sets the stop event to prevent the end of the song state from occurring

        if self.player: #stops if the player is playing 
            self.player.stop()

        self.stop_event.clear() # resets the state of the player
        self.is_paused = False

        self._play_next()# plays the next song
         
    def add_all_songs(self):
        added = 0
        for filename in os.listdir(self.music_dir):
                if filename.lower().endswith(('.mp3', '.wav', '.ogg','.flac')):
                    full_path = os.path.join(self.music_dir, filename)
                    self.queue.append(full_path)
                added += 1
        print(f"Added {added} songs from {self.music_dir} to the queue")

    def clear_queue(self):
        cleared = 0
        while not self.queue.empty():
            self.queue.get()
            self.queue.task_done()
            cleared += 1
        print(f"Cleared {cleared} queued songs")

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
            print("Queue Finished")
            return
        
        song = self.queue.popleft()
        print(f"Now Playing: {os.path.basename(song)}")

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


    def play(self):
        if self.is_playing and self.is_paused:
            self.player.play()
            self.is_paused = False
            print("resumed")
            return
        

        self.stop_event.clear()

        if not self.queue:
            self.add_all_songs()

        if not self.queue:
            print("No songs to play.")
            return
        
        self.is_playing = True
        self._play_next()

    def pause(self):
        if not self.is_playing:
            print("Nothing is playing")
            return
        
        if self.is_paused:
            self.player.play()
            self.is_paused = False
            print("resumed")
        else:
            self.player.pause()
            self.is_paused =True
            print("paused.")

    def stop(self):
        with self.lock:
            if self.player:
                self.player.stop()
            self.paused = False
            self.stop_event.set()
            print("playback stopped.")


    def set_volume(self, volume):
        if not 0 <= volume <= 100:
            print("volume must be between 1 and 100")
            return
        with self.lock:
            self.volume = volume
            if self.player:
                self.player.audio_set_volume(volume)
        print(f"Volume set to {volume}")

def command_loop(player):
    print("CLI Music Player")
    print("Commands: ")
    print("play | pause | stop | skip | shuffle | add")
    print("volume <0-100>")
    print("list")
    print("quit")

    while True:
        try:
            raw = input("> ").strip()
        except(EOFError,KeyboardInterrupt):
            print("\nExiting...")
            player.stop()
            break
        
        if not raw:
            continue 
        parts = raw.split(maxsplit=1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else None

        if command == "play":
            player.play()
        elif command == "pause":
            player.pause()
        elif command == "stop":
            player.stop()
        elif command == "add" and argument:
            player.add_to_queue(argument)
        elif command == "volume" and argument:
            player.set_volume(int(argument))
        elif command == "list":
            player.list_queue()
        elif command == "skip":
            player.skip()
        elif command == "shuffle":
            player.shuffle()
        elif command == "clear":
            player.clear_screen()
        elif command in ("quit","exit"):
            player.stop()
            break
        else:
            print("Unknown Command")


    
def main():
    parser = argparse.ArgumentParser(description="CLI Music Player")
    parser.add_argument("music_dir", help="path to your music directory")
    args = parser.parse_args()

    if not os.path.isdir(args.music_dir): 
        print("Invalid music directory")
        return
    player = MusicPlayer(args.music_dir)
    
    command_loop(player)
    

if __name__ == "__main__":
    main()




