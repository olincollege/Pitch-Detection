import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from karaoke_gui_clean import KaraokeModel, KaraokeView, KaraokeController, AudioRecorder
from PyQt5.QtWidgets import QApplication


class KaraokeModelTest(unittest.TestCase):
    def test_list_songs_returns_only_mp4(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "song1.mp4").write_text("dummy")
            (root / "notes.txt").write_text("ignore")
            model = KaraokeModel(figures_dir=root)
            songs = model.list_songs()
            self.assertEqual(songs, ["song1.mp4"])

    def test_set_selected_song_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "track.mp4").write_text("dummy")
            model = KaraokeModel(figures_dir=root)
            self.assertTrue(model.set_selected_song("track.mp4"))
            self.assertEqual(model.selected_song, "track.mp4")
            self.assertFalse(model.set_selected_song("missing.mp4"))

    def test_save_recording_writes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model = KaraokeModel(figures_dir=root)
            recording = np.zeros((4410, 1), dtype="float32")
            target = root / "saved_recording.wav"
            result = model.save_recording(recording, target)
            self.assertTrue(result)
            self.assertTrue(target.exists())


class KaraokeViewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication(sys.argv)

    def test_set_song_list_populates_widget(self):
        model = KaraokeModel(figures_dir=Path("."))
        view = KaraokeView(model)
        view.set_song_list(["first.mp4", "second.mp4"])
        self.assertEqual(view.song_list.count(), 2)
        view.song_list.setCurrentRow(1)
        self.assertEqual(view.get_selected_song_name(), "second.mp4")

    def test_load_video_updates_label(self):
        model = KaraokeModel(figures_dir=Path("."))
        view = KaraokeView(model)
        view.load_video(str(Path(__file__)))
        self.assertIn("Loaded:", view.video_label.text())


class KaraokeControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication(sys.argv)

    def setUp(self):
        model = KaraokeModel(figures_dir=Path("."))
        view = KaraokeView(model)
        self.controller = KaraokeController(model, view)
        self.view = view
        self.model = model

    def test_on_play_without_selection_sets_status(self):
        self.controller.on_play()
        self.assertEqual(self.view.status_label.text(), "Select a song before pressing Play")

    def test_on_playback_recording_without_recording_sets_status(self):
        self.controller.on_playback_recording()
        self.assertEqual(self.view.status_label.text(), "No recording available")

    def test_on_stop_reset_state(self):
        self.controller.is_playing = True
        self.controller.is_recording = True
        self.view.play_button.setText("Pause")
        self.view.record_button.setText("Stop Recording")
        self.controller.on_stop()
        self.assertFalse(self.controller.is_playing)
        self.assertFalse(self.controller.is_recording)
        self.assertEqual(self.view.play_button.text(), "Play")
        self.assertEqual(self.view.record_button.text(), "Record")
        self.assertEqual(self.view.status_label.text(), "Ready")

    def test_on_song_selected_while_playing_stops_active_session(self):
        self.controller.is_playing = True
        self.controller.is_recording = True
        self.view.load_video = MagicMock()
        self.controller.on_stop = MagicMock()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "song.mp4"
            file_path.write_text("dummy")
            self.model.figures_dir = root
            self.model.songs = ["song.mp4"]
            self.controller.on_song_selected("song.mp4")
            self.controller.on_stop.assert_called_once()
            self.assertEqual(self.view.status_label.text(), "Selected: song.mp4")

    def test_load_songs_populates_view_list(self):
        self.model.list_songs = MagicMock(return_value=["first.mp4", "second.mp4"])
        self.controller.load_songs()
        self.assertEqual(self.view.song_list.count(), 2)
        self.assertEqual(self.view.song_list.item(0).text(), "first.mp4")

    @patch("karaoke_gui_clean.AudioRecorder.start")
    def test_on_record_starts_recording_and_playback(self, recorder_start_mock):
        self.model.selected_path = Path("/tmp/song.mp4")
        self.model.selected_song = "song.mp4"
        self.model.load_audio_track = MagicMock(return_value=True)
        self.controller._open_video_capture = MagicMock(return_value=True)
        self.view.timer.start = MagicMock()
        self.controller.video_timer.start = MagicMock()

        self.controller.on_record()

        recorder_start_mock.assert_called_once()
        self.assertTrue(self.controller.is_recording)
        self.assertEqual(self.view.record_button.text(), "Stop Recording")
        self.assertEqual(self.view.play_button.text(), "Pause")

    @patch("karaoke_gui_clean.sd.play")
    def test_on_play_with_selection_starts_playback(self, sd_play_mock):
        self.model.selected_path = Path("/tmp/song.mp4")
        self.model.selected_song = "song.mp4"
        self.model.audio_data = np.zeros((44100, 2), dtype="float32")
        self.model.sample_rate = 44100
        self.model.load_audio_track = MagicMock(return_value=True)
        self.controller._open_video_capture = MagicMock(return_value=True)
        self.controller._show_next_frame = MagicMock()
        self.view.timer.start = MagicMock()
        self.controller.on_play()
        sd_play_mock.assert_called_once()
        self.view.timer.start.assert_called_once_with(100)
        self.assertTrue(self.controller.is_playing)

    @patch("karaoke_gui_clean.time.monotonic", return_value=1.1)
    def test_pause_playback_records_position(self, monotonic_mock):
        self.controller.play_start_time = 1.0
        self.controller.seek_start_ms = 200
        self.controller.video_capture = MagicMock()
        self.controller.video_capture.get.return_value = 250
        self.controller.view.timer.stop = MagicMock()
        self.controller.video_timer.stop = MagicMock()
        self.controller.pause_playback()
        self.assertTrue(self.controller.is_paused)
        self.assertEqual(self.view.play_button.text(), "Play")
        self.assertEqual(self.controller.playback_position_ms, 300)

    @patch("karaoke_gui_clean.sd.InputStream")
    def test_audio_recorder_start_and_stop(self, input_stream_mock):
        stream_instance = MagicMock()
        input_stream_mock.return_value = stream_instance
        recorder = AudioRecorder(sample_rate=44100, channels=1)
        recorder.start()
        self.assertTrue(input_stream_mock.called)
        recorder.stop()
        stream_instance.stop.assert_called_once()
        stream_instance.close.assert_called_once()

    @patch("karaoke_gui_clean.sd.play")
    def test_on_playback_recording_mixes_original_and_recorded_audio(self, sd_play_mock):
        self.model.selected_path = Path("/tmp/song.mp4")
        self.model.selected_song = "song.mp4"
        self.model.audio_data = np.zeros((44100 * 4, 2), dtype=np.float32)
        self.model.sample_rate = 44100
        self.model.recording_rate = 44100
        self.model.recorded_audio = np.ones((44100 * 2, 1), dtype=np.float32) * 0.5
        self.model.load_audio_track = MagicMock(return_value=True)
        self.controller._open_video_capture = MagicMock(return_value=True)
        self.controller._show_next_frame = MagicMock()
        self.view.timer.start = MagicMock()
        self.controller.video_timer.start = MagicMock()
        self.view.update_progress = MagicMock()
        self.controller.video_length_ms = 1000
        self.controller.playback_position_ms = 1000  # Set to non-zero to test reset

        playback_order = []

        def frame_side_effect():
            playback_order.append("frame")
            self.assertTrue(sd_play_mock.called, "Audio should start before the first video frame")

        self.controller._show_next_frame = MagicMock(side_effect=frame_side_effect)

        self.controller.on_playback_recording()

        # Verify it resets to start and clears progress to the beginning
        self.assertEqual(self.controller.playback_position_ms, 0)
        self.view.update_progress.assert_any_call(0, 1000)
        sd_play_mock.assert_called_once()
        self.assertEqual(playback_order, ["frame"])
        mixed_audio, sample_rate = sd_play_mock.call_args[0]
        self.assertEqual(sample_rate, 44100)
        self.assertEqual(mixed_audio.ndim, 2)
        self.assertEqual(mixed_audio.shape, (44100 * 4, 2))  # Full length since restarted
        # Check normalization and mix: recorded waveform set to RMS 0.15, then mixed
        expected_recorded = 0.15
        expected_mix = expected_recorded * 0.9
        self.assertTrue(np.allclose(mixed_audio[:44100*2, :], expected_mix))
        self.assertTrue(np.allclose(mixed_audio[44100*2:, :], 0.0))

    def test_recording_is_resampled_to_match_playback_rate(self):
        self.model.selected_path = Path("/tmp/song.mp4")
        self.model.selected_song = "song.mp4"
        self.model.audio_data = np.zeros((44100 * 4, 2), dtype=np.float32)
        self.model.sample_rate = 44100
        self.model.recording_rate = 22050
        self.model.recorded_audio = np.ones((22050 * 2, 1), dtype=np.float32) * 0.5

        mixed_audio = self.controller._prepare_combined_audio(0)

        self.assertIsNotNone(mixed_audio)
        self.assertEqual(mixed_audio.shape, (44100 * 4, 2))
        self.assertEqual(self.model.sample_rate, 44100)
        self.assertTrue(np.allclose(mixed_audio[:44100, :], 0.135, atol=1e-3))


if __name__ == "__main__":
    unittest.main()
