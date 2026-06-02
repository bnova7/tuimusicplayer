import os
import unittest
from collections import deque
from unittest.mock import MagicMock, patch, call


# Patch vlc before importing player so the module loads without VLC installed
vlc_mock = MagicMock()
vlc_mock.EventType.MediaPlayerEndReached = 1

with patch.dict("sys.modules", {"vlc": vlc_mock}):
    from player import MusicPlayer
    import player as _player_module


def make_player(tmp_path, songs=None):
    if songs:
        for name in songs:
            open(os.path.join(tmp_path, name), "w").close()
    with patch.dict("sys.modules", {"vlc": vlc_mock}):
        p = MusicPlayer(tmp_path)
    p.instance = MagicMock()
    p.player = MagicMock()
    return p


def console_output(mock_print):
    """Return all text passed to a patched console.print as a single string."""
    return " ".join(str(a) for call in mock_print.call_args_list for a in call[0])


class TestAddToQueue(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_valid_song_added(self):
        open(os.path.join(self.tmp, "song.mp3"), "w").close()
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.add_to_queue("song.mp3")
        self.assertIn(os.path.join(self.tmp, "song.mp3"), p.queue)

    def test_missing_song_raises(self):
        p = make_player(self.tmp)
        with self.assertRaises(FileNotFoundError):
            p.add_to_queue("ghost.mp3")


class TestAddAllSongs(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_loads_supported_formats(self):
        for name in ["a.mp3", "b.wav", "c.ogg", "d.flac"]:
            open(os.path.join(self.tmp, name), "w").close()
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.add_all_songs()
        basenames = [os.path.basename(s) for s in p.queue]
        self.assertIn("a.mp3", basenames)
        self.assertIn("b.wav", basenames)
        self.assertIn("c.ogg", basenames)
        self.assertIn("d.flac", basenames)

    def test_ignores_unsupported_formats(self):
        open(os.path.join(self.tmp, "notes.txt"), "w").close()
        open(os.path.join(self.tmp, "image.png"), "w").close()
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.add_all_songs()
        basenames = [os.path.basename(s) for s in p.queue]
        self.assertNotIn("notes.txt", basenames)
        self.assertNotIn("image.png", basenames)


class TestListQueue(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_empty_queue_message(self):
        from io import StringIO
        p = make_player(self.tmp)
        with patch("sys.stdout", new_callable=StringIO) as out:
            p.list_queue()
        self.assertIn("empty", out.getvalue())

    def test_lists_songs(self):
        from io import StringIO
        p = make_player(self.tmp)
        p.queue = deque(["/music/a.mp3", "/music/b.mp3"])
        with patch("sys.stdout", new_callable=StringIO) as out:
            p.list_queue()
        output = out.getvalue()
        self.assertIn("a.mp3", output)
        self.assertIn("b.mp3", output)


class TestShuffle(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        for name in ["a.mp3", "b.mp3", "c.mp3", "d.mp3", "e.mp3"]:
            open(os.path.join(self.tmp, name), "w").close()

    def test_queue_is_shuffled(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.queue = deque(["/m/a.mp3", "/m/b.mp3", "/m/c.mp3", "/m/d.mp3", "/m/e.mp3"])
        original = list(p.queue)
        import random
        random.seed(42)
        with patch.object(_player_module.console, "print"):
            p.shuffle()
        self.assertEqual(sorted(p.queue), sorted(original))

    def test_auto_loads_when_queue_empty(self):
        p = make_player(self.tmp)
        p.is_playing = True
        with patch.object(_player_module.console, "print"):
            p.shuffle()
        self.assertGreater(len(p.queue), 0)

    def test_starts_playing_when_not_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        p.queue = deque([os.path.join(self.tmp, "a.mp3")])
        with patch.object(p, "_play_next") as mock_play, \
             patch.object(_player_module.console, "print"):
            p.shuffle()
        mock_play.assert_called_once()


class TestPlay(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        open(os.path.join(self.tmp, "song.mp3"), "w").close()

    def test_resumes_when_paused(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.is_paused = True
        with patch.object(_player_module.console, "print"):
            p.play()
        p.player.play.assert_called()
        self.assertFalse(p.is_paused)

    def test_auto_loads_songs_when_queue_empty(self):
        p = make_player(self.tmp)
        with patch.object(p, "add_all_songs") as mock_load, \
             patch.object(p, "_play_next"), \
             patch.object(_player_module.console, "print"):
            p.queue = deque()
            p.play()
        mock_load.assert_called_once()

    def test_prints_error_when_no_songs(self):
        p = make_player(self.tmp)
        p.queue = deque()
        with patch.object(p, "add_all_songs"), \
             patch.object(_player_module.console, "print") as mock_print:
            p.play()
        self.assertIn("No songs", console_output(mock_print))


class TestPause(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_pauses_when_playing(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.is_paused = False
        with patch.object(_player_module.console, "print"):
            p.pause()
        p.player.pause.assert_called_once()
        self.assertTrue(p.is_paused)

    def test_resumes_when_already_paused(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.is_paused = True
        with patch.object(_player_module.console, "print"):
            p.pause()
        p.player.play.assert_called_once()
        self.assertFalse(p.is_paused)

    def test_error_when_nothing_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        with patch.object(_player_module.console, "print") as mock_print:
            p.pause()
        self.assertIn("Nothing", console_output(mock_print))


class TestSkip(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_skip_when_playing(self):
        p = make_player(self.tmp)
        p.is_playing = True
        with patch.object(p, "_play_next") as mock_next, \
             patch.object(_player_module.console, "print"):
            p.skip()
        p.player.stop.assert_called_once()
        mock_next.assert_called_once()

    def test_skip_when_not_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        with patch.object(_player_module.console, "print") as mock_print:
            p.skip()
        self.assertIn("nothing", console_output(mock_print).lower())


class TestStop(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_stop_calls_player_stop(self):
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.stop()
        p.player.stop.assert_called_once()

    def test_stop_sets_stop_event(self):
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.stop()
        self.assertTrue(p.stop_event.is_set())


class TestSetVolume(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_valid_volume(self):
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.set_volume(50)
        self.assertEqual(p.volume, 50)
        p.player.audio_set_volume.assert_called_with(50)

    def test_boundary_values(self):
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print"):
            p.set_volume(0)
            self.assertEqual(p.volume, 0)
            p.set_volume(100)
            self.assertEqual(p.volume, 100)

    def test_rejects_out_of_range(self):
        p = make_player(self.tmp)
        p.volume = 50
        with patch.object(_player_module.console, "print"):
            p.set_volume(101)
            p.set_volume(-1)
        self.assertEqual(p.volume, 50)


class TestCommandLoop(unittest.TestCase):
    def _run_commands(self, player, commands):
        from main import command_loop
        inputs = iter(commands + ["quit"])
        with patch("rich.prompt.Prompt.ask", side_effect=inputs), \
             patch("main.console.print"):
            command_loop(player)

    def setUp(self):
        self.player = MagicMock()
        self.player.queue = deque()

    def test_play(self):
        self._run_commands(self.player, ["play"])
        self.player.play.assert_called_once()

    def test_pause(self):
        self._run_commands(self.player, ["pause"])
        self.player.pause.assert_called_once()

    def test_stop(self):
        self._run_commands(self.player, ["stop"])
        self.player.stop.assert_called()

    def test_skip(self):
        self._run_commands(self.player, ["skip"])
        self.player.skip.assert_called_once()

    def test_shuffle(self):
        self._run_commands(self.player, ["shuffle"])
        self.player.shuffle.assert_called_once()

    def test_list(self):
        from main import command_loop
        inputs = iter(["list", "quit"])
        with patch("rich.prompt.Prompt.ask", side_effect=inputs), \
             patch("main.console.print"), \
             patch("main.print_queue") as mock_print_queue:
            command_loop(self.player)
        mock_print_queue.assert_called_once_with(self.player.queue)

    def test_add(self):
        self._run_commands(self.player, ["add song.mp3"])
        self.player.add_to_queue.assert_called_once_with("song.mp3")

    def test_volume(self):
        self._run_commands(self.player, ["volume 75"])
        self.player.set_volume.assert_called_once_with(75)

    def test_unknown_command(self):
        from main import command_loop
        inputs = iter(["badcmd", "quit"])
        with patch("rich.prompt.Prompt.ask", side_effect=inputs), \
             patch("main.console.print") as mock_print:
            command_loop(self.player)
        self.assertIn("Unknown", console_output(mock_print))

    def test_quit_stops_player(self):
        from main import command_loop
        inputs = iter(["quit"])
        with patch("rich.prompt.Prompt.ask", side_effect=inputs), \
             patch("main.console.print"):
            command_loop(self.player)
        self.player.stop.assert_called_once()


class TestSearchSong(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_returns_matching_songs(self):
        open(os.path.join(self.tmp, "rockstar.mp3"), "w").close()
        open(os.path.join(self.tmp, "jazz.mp3"), "w").close()
        p = make_player(self.tmp)
        results = p.search_song("rock")
        self.assertIn("rockstar.mp3", results)
        self.assertNotIn("jazz.mp3", results)

    def test_case_insensitive(self):
        open(os.path.join(self.tmp, "Rockstar.mp3"), "w").close()
        p = make_player(self.tmp)
        results = p.search_song("ROCK")
        self.assertIn("Rockstar.mp3", results)

    def test_returns_empty_when_no_match(self):
        open(os.path.join(self.tmp, "jazz.mp3"), "w").close()
        p = make_player(self.tmp)
        results = p.search_song("classical")
        self.assertEqual(results, [])

    def test_ignores_non_audio_files(self):
        open(os.path.join(self.tmp, "rock.txt"), "w").close()
        p = make_player(self.tmp)
        results = p.search_song("rock")
        self.assertNotIn("rock.txt", results)


class TestCreatePlaylist(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_creates_new_playlist(self):
        p = make_player(self.tmp)
        with patch.object(_player_module, "write_to_playlists"), \
             patch.object(_player_module.console, "print"):
            p.create_playlist("chill")
        self.assertIn("chill", p.playlists)
        self.assertEqual(p.playlists["chill"], [])

    def test_rejects_duplicate_name(self):
        p = make_player(self.tmp)
        p.playlists["chill"] = []
        with patch.object(_player_module, "write_to_playlists") as mock_write, \
             patch.object(_player_module.console, "print"):
            p.create_playlist("chill")
        mock_write.assert_not_called()

    def test_saves_to_file(self):
        p = make_player(self.tmp)
        with patch.object(_player_module, "write_to_playlists") as mock_write, \
             patch.object(_player_module.console, "print"):
            p.create_playlist("chill")
        mock_write.assert_called_once()


class TestAddToPlaylist(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        open(os.path.join(self.tmp, "song.mp3"), "w").close()

    def test_adds_song_to_existing_playlist(self):
        p = make_player(self.tmp)
        p.playlists["chill"] = []
        with patch.object(_player_module, "write_to_playlists"), \
             patch.object(_player_module.console, "print"):
            p.add_to_playlist("chill", "song.mp3")
        self.assertEqual(len(p.playlists["chill"]), 1)
        self.assertIn("song.mp3", os.path.basename(p.playlists["chill"][0]))

    def test_does_nothing_when_playlist_missing(self):
        p = make_player(self.tmp)
        with patch.object(_player_module, "write_to_playlists") as mock_write, \
             patch.object(_player_module.console, "print"):
            p.add_to_playlist("nonexistent", "song.mp3")
        mock_write.assert_not_called()

    def test_saves_to_file_after_adding(self):
        p = make_player(self.tmp)
        p.playlists["chill"] = []
        with patch.object(_player_module, "write_to_playlists") as mock_write, \
             patch.object(_player_module.console, "print"):
            p.add_to_playlist("chill", "song.mp3")
        mock_write.assert_called_once()


class TestDeletePlaylist(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_deletes_existing_playlist(self):
        p = make_player(self.tmp)
        p.playlists["chill"] = []
        with patch.object(_player_module, "write_to_playlists"), \
             patch.object(_player_module.console, "print"):
            p.delete_playlist("chill")
        self.assertNotIn("chill", p.playlists)

    def test_error_when_not_found(self):
        p = make_player(self.tmp)
        with patch.object(_player_module, "write_to_playlists") as mock_write, \
             patch.object(_player_module.console, "print") as mock_print:
            p.delete_playlist("nonexistent")
        mock_write.assert_not_called()
        self.assertIn("not found", console_output(mock_print).lower())


class TestPlayPlaylist(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        open(os.path.join(self.tmp, "song.mp3"), "w").close()

    def test_loads_playlist_into_queue(self):
        p = make_player(self.tmp)
        song_path = os.path.join(self.tmp, "song.mp3")
        p.playlists["chill"] = [song_path]
        with patch.object(p, "play"), \
             patch.object(_player_module.console, "print"):
            p.play_playlist("chill")
        self.assertIn(song_path, p.queue)

    def test_error_when_not_found(self):
        p = make_player(self.tmp)
        with patch.object(_player_module.console, "print") as mock_print:
            p.play_playlist("nonexistent")
        self.assertIn("not found", console_output(mock_print).lower())


if __name__ == "__main__":
    unittest.main()
