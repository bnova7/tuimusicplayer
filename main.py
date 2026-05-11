import argparse
import os
import subprocess

from player import MusicPlayer


def clear_screen():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)


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
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            player.stop()
            break

        if not raw:
            continue
        parts = raw.split(maxsplit=1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else None

        if command == "play":
            player.play(argument)
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
            clear_screen()
        elif command in ("quit", "exit"):
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
