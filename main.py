import argparse
import os
import subprocess

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from player import MusicPlayer

console = Console()


def clear_screen():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)


def print_queue(queue):
    if not queue:
        console.print("[yellow]Queue is empty.[/yellow]")
        return
    table = Table(title="Queue", border_style="cyan", header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Song", style="white")
    for i, song in enumerate(queue, 1):
        table.add_row(str(i), os.path.basename(song))
    console.print(table)


def command_loop(player):
    console.print(Panel.fit(
        "[bold cyan]CLI Music Player[/bold cyan]\n\n"
        "[green]play[/green] | [green]pause[/green] | [green]stop[/green] | [green]skip[/green] | [green]shuffle[/green] | [green]add <file>[/green] | [green]empty[/green]\n"
        "[green]volume <0-100>[/green] | [green]list[/green] | [green] search [/green] | [green]clear[/green] | [green]playlist[/green] | [green]quit[/green]",
        title="Commands",
        border_style="cyan"
    ))

    while True:
        try:
            raw = Prompt.ask("[bold cyan]>[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Exiting...[/yellow]")
            player.stop()
            break

        if not raw:
            continue
        parts = raw.split(maxsplit=3)
        command = parts[0]
        subcommand = parts[1] if len(parts) > 1 else None
        argument = parts[2] if len(parts) > 2 else None
        song_name = parts[3] if len(parts) > 3 else None

        if command == "play":
            player.play(argument)
        elif command == "pause":
            player.pause()
        elif command == "stop":
            player.stop()
        elif command == "playlist" and not subcommand and not argument:
            console.print("[green]Playlist commands:[/green] create <name>, add <playlist> <song>, play <playlist>, list <playlist> , delete <playlist>")
        elif command == "playlist" and subcommand == "add" and argument and song_name:
            player.add_to_playlist(argument, song_name)
        elif command == "playlist" and subcommand == "play" and argument:
            player.play_playlist(argument)
        elif command == "playlist" and subcommand == "list" and argument:
            player.list_playlists(argument)
        elif command == "playlist" and subcommand == "delete" and argument:
            player.delete_playlist(argument)
        elif command == "playlist" and subcommand == "create" and argument:
            player.create_playlist(argument)
        elif command == "add" and argument:
            player.add_to_queue(argument)
        elif command == "volume" and argument:
            player.set_volume(int(argument))
        elif command == "list":
            print_queue(player.queue)
        elif command == "skip":
            player.skip()
        elif command == "shuffle":
            player.shuffle()
        elif command == "search":
            if not argument:
                console.print("[red] Please provide an argument [/red]" \
                "[green]Usage:[/green] search <query>")
            else:
                player.search_song(argument)
                console.print(f"[green]Search results for:[/green] {argument}")
                console.print(player.search_song(argument))
        elif command == "clear":
            clear_screen()
        elif command == "empty":
            player.clear_queue()
        elif command in ("quit", "exit"):
            player.stop()
            break
        else:
            console.print("[red]Unknown command.[/red]")


def main():
    parser = argparse.ArgumentParser(description="CLI Music Player")
    parser.add_argument("music_dir", help="path to your music directory")
    args = parser.parse_args()

    if not os.path.isdir(args.music_dir):
        console.print("[red]Invalid music directory.[/red]")
        return
    player = MusicPlayer(args.music_dir)

    command_loop(player)


if __name__ == "__main__":
    main()
