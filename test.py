import os
import unittest
from collections import deque
from unittest.mock import MagicMock, patch
from io import StringIO


# Patch vlc before importing player so the module loads without VLC installed
vlc_mock = MagicMock()
vlc_mock.EventType.MediaPlayerEndReached = 1

with patch.dict("sys.modules", {"vlc": vlc_mock}):
    from player import MusicPlayer


def make_player(tmp_path, songs=None):
    """Create a MusicPlayer pointed at tmp_path, optionally pre-populate the dir."""
    if songs:
        for name in songs:
            open(os.path.join(tmp_path, name), "w").close()
    with patch.dict("sys.modules", {"vlc": vlc_mock}):
        p = MusicPlayer(tmp_path)
    p.instance = MagicMock()
    p.player = MagicMock()
    return p


class TestAddToQueue(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_valid_song_added(self):
        open(os.path.join(self.tmp, "song.mp3"), "w").close()
        p = make_player(self.tmp)
        p.add_to_queue("song.mp3")
        self.assertIn("song.mp3", p.queue)

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
        p.add_all_songs()
        basenames = [os.path.basename(s) for s in p.queue]
        self.assertNotIn("notes.txt", basenames)
        self.assertNotIn("image.png", basenames)


class TestListQueue(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_empty_queue_message(self):
        p = make_player(self.tmp)
        with patch("sys.stdout", new_callable=StringIO) as out:
            p.list_queue()
        self.assertIn("empty", out.getvalue())

    def test_lists_songs(self):
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
        p.shuffle()
        self.assertEqual(sorted(p.queue), sorted(original))

    def test_auto_loads_when_queue_empty(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.shuffle()
        self.assertGreater(len(p.queue), 0)

    def test_starts_playing_when_not_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        p.queue = deque([os.path.join(self.tmp, "a.mp3")])
        with patch.object(p, "_play_next") as mock_play:
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
        p.play()
        p.player.play.assert_called()
        self.assertFalse(p.is_paused)

    def test_auto_loads_songs_when_queue_empty(self):
        p = make_player(self.tmp)
        with patch.object(p, "add_all_songs") as mock_load, \
             patch.object(p, "_play_next"):
            p.queue = deque()
            p.play()
        mock_load.assert_called_once()

    def test_prints_error_when_no_songs(self):
        p = make_player(self.tmp)
        p.queue = deque()
        with patch.object(p, "add_all_songs"):
            with patch("sys.stdout", new_callable=StringIO) as out:
                p.play()
        self.assertIn("No songs", out.getvalue())


class TestPause(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_pauses_when_playing(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.is_paused = False
        p.pause()
        p.player.pause.assert_called_once()
        self.assertTrue(p.is_paused)

    def test_resumes_when_already_paused(self):
        p = make_player(self.tmp)
        p.is_playing = True
        p.is_paused = True
        p.pause()
        p.player.play.assert_called_once()
        self.assertFalse(p.is_paused)

    def test_error_when_nothing_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        with patch("sys.stdout", new_callable=StringIO) as out:
            p.pause()
        self.assertIn("Nothing", out.getvalue())


class TestSkip(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_skip_when_playing(self):
        p = make_player(self.tmp)
        p.is_playing = True
        with patch.object(p, "_play_next") as mock_next:
            p.skip()
        p.player.stop.assert_called_once()
        mock_next.assert_called_once()

    def test_skip_when_not_playing(self):
        p = make_player(self.tmp)
        p.is_playing = False
        with patch("sys.stdout", new_callable=StringIO) as out:
            p.skip()
        self.assertIn("nothing", out.getvalue().lower())


class TestStop(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_stop_calls_player_stop(self):
        p = make_player(self.tmp)
        p.stop()
        p.player.stop.assert_called_once()

    def test_stop_sets_stop_event(self):
        p = make_player(self.tmp)
        p.stop()
        self.assertTrue(p.stop_event.is_set())


class TestSetVolume(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()

    def test_valid_volume(self):
        p = make_player(self.tmp)
        p.set_volume(50)
        self.assertEqual(p.volume, 50)
        p.player.audio_set_volume.assert_called_with(50)

    def test_boundary_values(self):
        p = make_player(self.tmp)
        p.set_volume(0)
        self.assertEqual(p.volume, 0)
        p.set_volume(100)
        self.assertEqual(p.volume, 100)

    def test_rejects_out_of_range(self):
        p = make_player(self.tmp)
        p.volume = 50
        with patch("sys.stdout", new_callable=StringIO):
            p.set_volume(101)
            p.set_volume(-1)
        self.assertEqual(p.volume, 50)


class TestCommandLoop(unittest.TestCase):
    def _run_commands(self, player, commands):
        from main import command_loop
        inputs = iter(commands + ["quit"])
        with patch("builtins.input", side_effect=inputs), \
             patch("sys.stdout", new_callable=StringIO):
            command_loop(player)

    def setUp(self):
        self.player = MagicMock()

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
        self._run_commands(self.player, ["list"])
        self.player.list_queue.assert_called_once()

    def test_add(self):
        self._run_commands(self.player, ["add song.mp3"])
        self.player.add_to_queue.assert_called_once_with("song.mp3")

    def test_volume(self):
        self._run_commands(self.player, ["volume 75"])
        self.player.set_volume.assert_called_once_with(75)

    def test_unknown_command(self):
        from main import command_loop
        inputs = iter(["badcmd", "quit"])
        with patch("builtins.input", side_effect=inputs), \
             patch("sys.stdout", new_callable=StringIO) as out:
            command_loop(self.player)
        self.assertIn("Unknown", out.getvalue())

    def test_quit_stops_player(self):
        from main import command_loop
        inputs = iter(["quit"])
        with patch("builtins.input", side_effect=inputs), \
             patch("sys.stdout", new_callable=StringIO):
            command_loop(self.player)
        self.player.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
