# -*- coding: utf-8 -*-
"""
Karaoke app using a clean Model-View-Controller architecture.

This module provides the karaoke application model, view, and controller.
The app uses MP4 videos from the project's Figures folder as song sources.
Users can select a song, play the video, record their voice while the video plays,
and then playback both the original track and their recording together.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import cv2
import imageio_ffmpeg as ffmpeg
import numpy as np
import sounddevice as sd
import soundfile as sf
import subprocess
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = PROJECT_ROOT / "Figures"
RECORDING_FILE = PROJECT_ROOT / "recording.wav"
SUPPORTED_EXTENSIONS = [".mp4"]


# KaraokeModel class starts here
class KaraokeModel:
    """Model that tracks song selection, audio data, and recorded vocals."""

    def __init__(self, figures_dir: Path = FIGURES_DIR):
        """Initialize the karaoke model with the figures directory.

        Args:
            figures_dir (Path): The directory containing MP4 files. Defaults to FIGURES_DIR.

        Returns:
            None
        """
        self.figures_dir = Path(figures_dir)
        self.songs: List[str] = self.list_songs()
        self.selected_song: Optional[str] = None
        self.selected_path: Optional[Path] = None
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: int = 0
        self.recorded_audio: Optional[np.ndarray] = None
        self.recording_rate: int = 44100

    def list_songs(self) -> List[str]:
        """Return the list of available MP4 song files.

        Returns:
            A sorted list of MP4 filenames found in the Figures directory.
        """
        if not self.figures_dir.exists():
            return []
        return sorted(
            [
                entry.name
                for entry in self.figures_dir.iterdir()
                if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
        )

    def set_selected_song(self, song_name: str) -> bool:
        """Select the named song if the file exists.

        Args:
            song_name: The filename of the song to select.

        Returns:
            True if the song exists and was selected; otherwise False.
        """
        candidate = self.figures_dir / song_name
        if candidate.is_file():
            self.selected_song = song_name
            self.selected_path = candidate
            self.audio_data = None
            self.sample_rate = 0
            return True
        return False

    def load_audio_track(self) -> bool:
        """Extract the MP4 audio track using FFmpeg and cache it as stereo audio.

        The extracted audio is resampled to the model recording rate and preserved
        as a two-channel waveform so playback matches the original MP4 audio.

        Returns:
            True if audio was extracted successfully; otherwise False.
        """
        if self.selected_path is None:
            return False
        try:
            ffmpeg_exe = ffmpeg.get_ffmpeg_exe()
            command = [
                ffmpeg_exe,
                "-i",
                str(self.selected_path),
                "-vn",
                "-ac",
                "2",
                "-ar",
                str(self.recording_rate),
                "-f",
                "f32le",
                "-",
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0 or not result.stdout:
                self.audio_data = None
                self.sample_rate = 0
                return False
            audio = np.frombuffer(result.stdout, dtype=np.float32)
            if audio.size % 2 == 0:
                audio = audio.reshape(-1, 2)
            self.audio_data = audio
            self.sample_rate = self.recording_rate
            return True
        except Exception:
            self.audio_data = None
            self.sample_rate = 0
            return False

    def save_recording(self, recording: np.ndarray, path: Optional[Path] = None) -> bool:
        """Save the recorded vocals to a WAV file and cache the data.

        Args:
            recording: The recorded waveform.
            path: Optional output path. Uses a default recording path if omitted.

        Returns:
            True if the file saved successfully; otherwise False.
        """
        target_path = Path(path) if path is not None else RECORDING_FILE
        try:
            sf.write(str(target_path), recording, self.recording_rate)
            self.recorded_audio = recording
            return True
        except Exception:
            return False

    def has_recording(self) -> bool:
        """Return True when a recording is available.

        Returns:
            True if a recording exists; otherwise False.
        """
        return self.recorded_audio is not None and len(self.recorded_audio) > 0


# AudioRecorder class starts here
class AudioRecorder:
    """Helper that records microphone input until stopped or paused."""

    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        """Initialize the audio recorder with sample rate and channels.

        Args:
            sample_rate (int): The sample rate for recording. Defaults to 44100.
            channels (int): The number of audio channels. Defaults to 1.

        Returns:
            None
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: List[np.ndarray] = []
        self._stream = None
        self._paused = False

    def start(self) -> None:
        """Open the input stream and begin recording immediately.

        Returns:
            None
        """
        self._frames = []
        self._paused = False
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback,
        )
        self._stream.start()

    def pause(self) -> None:
        """Pause incoming recording without losing captured audio.

        Returns:
            None
        """
        if self._stream is not None:
            self._paused = True

    def resume(self) -> None:
        """Resume recording after a pause.

        Returns:
            None
        """
        if self._stream is not None:
            self._paused = False

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            The captured audio as a numpy array.
        """
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._paused = False
        if not self._frames:
            return np.empty((0, self.channels), dtype="float32")
        return np.concatenate(self._frames, axis=0)

    def _callback(self, indata, _frames, _time, _status) -> None:
        if not self._paused:
            self._frames.append(np.copy(indata))


# KaraokeView class starts here
class KaraokeView(QWidget):
    """View layer that displays the song list, video widget, and player controls."""

    play_pressed = pyqtSignal()
    record_pressed = pyqtSignal()
    stop_pressed = pyqtSignal()
    playback_pressed = pyqtSignal()
    song_selected = pyqtSignal(str)

    def __init__(self, model: KaraokeModel):
        """Initialize the karaoke view with the model.

        Args:
            model (KaraokeModel): The model instance for the view.

        Returns:
            None
        """
        super().__init__()
        self.model = model
        self.setWindowTitle("Mister Microphone")
        self.setGeometry(100, 100, 1200, 900)
        self.video_label = QLabel("Select a song to load video")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self._build_ui()
        self.timer = QTimer(self)

    def _build_ui(self) -> None:
        """Create the main user interface widgets.

        Returns:
            None
        """
        self.song_list = QListWidget()
        self.song_list.currentItemChanged.connect(self._on_song_selection)

        heading = QLabel("Choose a song from the list and press Play")
        heading.setFont(QFont("Arial", 20, QFont.Bold))
        heading.setAlignment(Qt.AlignCenter)

        self.play_button = QPushButton("Play")
        self.record_button = QPushButton("Record")
        self.stop_button = QPushButton("Stop")
        self.playback_button = QPushButton("Playback Recording")

        self.play_button.clicked.connect(self.play_pressed.emit)
        self.record_button.clicked.connect(self.record_pressed.emit)
        self.stop_button.clicked.connect(self.stop_pressed.emit)
        self.playback_button.clicked.connect(self.playback_pressed.emit)

        control_layout = QHBoxLayout()
        for button in [self.play_button, self.record_button, self.stop_button, self.playback_button]:
            button.setMinimumHeight(50)
            control_layout.addWidget(button)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label)

        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("Available Songs"))
        list_layout.addWidget(self.song_list)

        main_layout = QVBoxLayout()
        main_layout.addWidget(heading)

        top_layout = QHBoxLayout()
        top_layout.addLayout(list_layout, 1)
        top_layout.addLayout(video_layout, 3)
        main_layout.addLayout(top_layout)

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.status_label)
        self.setLayout(main_layout)

    def _on_song_selection(self, current, previous=None) -> None:
        """Handle song selection from the view.

        Args:
            current: The currently selected item.
            previous: The previously selected item.

        Returns:
            None
        """
        item = self.song_list.currentItem()
        if item is not None:
            self.song_selected.emit(item.text())

    def set_song_list(self, songs: List[str]) -> None:
        """Populate the song list with available MP4 titles.

        Args:
            songs (List[str]): List of song filenames.

        Returns:
            None
        """
        self.song_list.clear()
        for song in songs:
            self.song_list.addItem(song)

    def get_selected_song_name(self) -> str:
        """Return the currently selected song title.

        Returns:
            The selected song name or empty string if none.
        """
        item = self.song_list.currentItem()
        return item.text() if item is not None else ""

    def set_status(self, text: str) -> None:
        """Update the status label text.

        Args:
            text (str): The status text to display.

        Returns:
            None
        """
        """Update the status label text."""
        self.status_label.setText(text)

    def load_video(self, path: str) -> None:
        """Show a placeholder for the selected video file.

        Args:
            path (str): The path to the video file.

        Returns:
            None
        """
        """Show a placeholder for the selected video file."""
        self.video_label.setText(f"Loaded: {Path(path).name}")
        self.video_label.setStyleSheet("background-color: black; color: white;")

    def set_video_frame(self, frame: np.ndarray) -> None:
        """Render a video frame into the video display widget.

        Args:
            frame (np.ndarray): The video frame as a numpy array.

        Returns:
            None
        """
        """Render a video frame into the video display widget."""
        target_width = self.video_label.width() or frame.shape[1]
        target_height = self.video_label.height() or frame.shape[0]
        if frame.shape[1] != target_width or frame.shape[0] != target_height:
            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap)

    def clear_video(self) -> None:
        """Clear the video display and show the default placeholder.

        Returns:
            None
        """
        """Clear the video display and show the default placeholder."""
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText("Select a song to load video")
        self.video_label.setStyleSheet("background-color: black; color: white;")

    def update_progress(self, position_ms: int, duration_ms: int) -> None:
        """Update the progress bar using media position and duration.

        Args:
            position_ms (int): Current position in milliseconds.
            duration_ms (int): Total duration in milliseconds.

        Returns:
            None
        """
        """Update the progress bar using media position and duration."""
        if duration_ms <= 0:
            return
        ratio = min(max(position_ms / duration_ms, 0.0), 1.0)
        self.progress.setValue(int(ratio * 100))
        current_seconds = position_ms // 1000
        duration_seconds = duration_ms // 1000
        self.status_label.setText(
            f"{current_seconds // 60:02d}:{current_seconds % 60:02d} / {duration_seconds // 60:02d}:{duration_seconds % 60:02d}"
        )


# KaraokeController class starts here
class KaraokeController:
    """Controller that coordinates model state and view interactions."""

    def __init__(self, model: KaraokeModel, view: KaraokeView):
        """Initialize the karaoke controller with model and view.

        Args:
            model (KaraokeModel): The model instance.
            view (KaraokeView): The view instance.

        Returns:
            None
        """
        self.model = model
        self.view = view
        self.view.play_pressed.connect(self.on_play)
        self.view.record_pressed.connect(self.on_record)
        self.view.stop_pressed.connect(self.on_stop)
        self.view.playback_pressed.connect(self.on_playback_recording)
        self.view.song_selected.connect(self.on_song_selected)
        self.view.timer.timeout.connect(self.update_ui)
        self.video_capture = None
        self.video_frame_interval = 40
        self.video_length_ms = 0
        self.video_timer = QTimer(self.view)
        self.video_timer.timeout.connect(self._show_next_frame)
        self.recorder = AudioRecorder(sample_rate=self.model.recording_rate, channels=1)
        self.is_playing = False
        self.is_paused = False
        self.is_recording = False
        self.record_paused = False
        self.playback_position_ms = 0
        self.play_start_time = 0.0
        self.seek_start_ms = 0

    def load_songs(self) -> None:
        """Load the available songs into the view list."""
        self.model.songs = self.model.list_songs()
        self.view.set_song_list(self.model.songs)
        if not self.model.songs:
            self.view.set_status("No songs found in the Figures folder")

    def on_song_selected(self, song_name: str) -> None:
        """Handle song selection from the view and reset active playback."""
        if self.is_playing or self.is_paused or self.is_recording:
            self.on_stop()
        if self.model.set_selected_song(song_name):
            self.view.load_video(str(self.model.selected_path))
            self.view.set_status(f"Selected: {song_name}")
            self.model.load_audio_track()
            self.playback_position_ms = 0
            self.view.clear_video()
        else:
            self.view.set_status("Unable to select song")

    def on_play(self) -> None:
        """Start playback, resume paused playback, or pause current playback."""
        if self.is_playing and not self.is_paused:
            self.pause_playback()
            return
        if self.is_paused:
            self.resume_playback()
            return
        if self.model.selected_path is None:
            self.view.set_status("Select a song before pressing Play")
            return
        self.start_playback()

    def _open_video_capture(self, start_ms: int = 0) -> bool:
        """Open the OpenCV video capture and set the desired start position."""
        if self.model.selected_path is None:
            return False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self.video_capture = cv2.VideoCapture(str(self.model.selected_path))
        if not self.video_capture.isOpened():
            self.view.set_status("Unable to open video file")
            return False
        fps = self.video_capture.get(cv2.CAP_PROP_FPS) or 25.0
        self.video_frame_interval = max(1, int(1000 / fps))
        frame_count = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        self.video_length_ms = int(frame_count / fps * 1000)
        self.video_timer.setInterval(self.video_frame_interval)
        if start_ms > 0:
            self.video_capture.set(cv2.CAP_PROP_POS_MSEC, float(start_ms))
        return True

    def start_playback(self) -> None:
        """Begin video playback and immediate audio output from the selected song."""
        if not self.model.load_audio_track():
            self.view.set_status("Unable to load audio track")
            return
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.seek_start_ms = self.playback_position_ms
        self.is_playing = True
        self.is_paused = False
        self.view.play_button.setText("Pause")
        self.view.timer.start(100)
        try:
            start_sample = int(round(self.playback_position_ms * self.model.sample_rate / 1000.0))
            sd.play(self.model.audio_data[start_sample:], self.model.sample_rate)
        except Exception:
            self.view.set_status("Audio playback failed")
            return
        self.play_start_time = time.monotonic()
        self.video_timer.start(self.video_frame_interval)
        self._show_next_frame()
        self.view.set_status("Playing")

    def resume_playback(self) -> None:
        """Resume playback from the point where it was paused."""
        if self.model.selected_path is None:
            self.view.set_status("Select a song before pressing Play")
            return
        if self.is_recording and self.record_paused:
            self.recorder.resume()
            self.record_paused = False
        self.start_playback()

    def pause_playback(self) -> None:
        """Pause the active playback session and preserve the current position."""
        if self.play_start_time > 0:
            elapsed_ms = int((time.monotonic() - self.play_start_time) * 1000)
            self.playback_position_ms = self.seek_start_ms + elapsed_ms
        elif self.video_capture is not None:
            self.playback_position_ms = int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC))
        self.play_start_time = 0.0
        self.video_timer.stop()
        self.view.timer.stop()
        sd.stop()
        self.is_playing = False
        self.is_paused = True
        self.view.play_button.setText("Play")
        self.view.set_status("Paused")
        if self.is_recording and not self.record_paused:
            self.recorder.pause()
            self.record_paused = True

    def on_stop(self) -> None:
        """Stop all playback and recording activity and reset playback state."""
        self.video_timer.stop()
        self.view.timer.stop()
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        sd.stop()
        if self.is_recording:
            self._stop_recording()
        self.is_playing = False
        self.is_paused = False
        self.record_paused = False
        self.playback_position_ms = 0
        self.view.play_button.setText("Play")
        self.view.record_button.setText("Record")
        self.view.set_status("Ready")
        self.view.clear_video()

    def on_record(self) -> None:
        """Start or stop recording the user's voice while the song plays."""
        if self.is_recording:
            self.on_stop()
            return
        if self.model.selected_path is None:
            self.view.set_status("Select a song before recording")
            return
        if not self.model.load_audio_track():
            self.view.set_status("Unable to load audio track")
            return
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.recorder.start()
        self.is_recording = True
        self.record_paused = False
        self.is_playing = True
        self.is_paused = False
        self.seek_start_ms = self.playback_position_ms
        self.view.record_button.setText("Stop Recording")
        self.view.play_button.setText("Pause")
        self.view.set_status("Recording...")
        self.view.timer.start(100)
        self.video_timer.start(self.video_frame_interval)
        try:
            start_sample = int(round(self.playback_position_ms * self.model.sample_rate / 1000.0))
            sd.play(self.model.audio_data[start_sample:], self.model.sample_rate)
        except Exception:
            self.view.set_status("Audio playback failed")
            return
        self.play_start_time = time.monotonic()
        self._show_next_frame()

    def _stop_recording(self) -> None:
        """Stop recording and save the captured audio to the model."""
        recording = self.recorder.stop()
        self.model.save_recording(recording)
        self.is_recording = False
        self.record_paused = False
        self.view.record_button.setText("Record")
        self.view.set_status("Recording saved")

    def on_playback_recording(self) -> None:
        """Play the selected video together with the user's saved recording from the start.

        Restarts the song and video from the beginning to ensure full playback with lyrics.
        The recorded vocal track is mixed with the original MP4 audio using balanced gains
        so both background music and voice are audible.
        """
        if not self.model.has_recording():
            self.view.set_status("No recording available")
            return
        if self.model.selected_path is None:
            self.view.set_status("Select a song before playback")
            return
        if self.is_playing or self.is_recording or self.is_paused:
            self.on_stop()
        self.view.clear_video()
        self.view.set_status("Select a song to start video")
        if not self.model.load_audio_track():
            self.view.set_status("Unable to load audio track")
            return
        self.playback_position_ms = 0
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.seek_start_ms = self.playback_position_ms
        self.is_playing = True
        self.is_paused = False
        self.view.play_button.setText("Pause")
        self.view.timer.start(100)
        mixed_audio = self._prepare_combined_audio(self.playback_position_ms)
        if mixed_audio is None:
            self.view.set_status("Unable to play combined audio")
            return
        try:
            sd.play(mixed_audio, self.model.sample_rate)
        except Exception:
            self.view.set_status("Playback of recording failed")
            return
        self.play_start_time = time.monotonic()
        self.video_timer.start(self.video_frame_interval)
        self.view.update_progress(0, self.video_length_ms)
        self._show_next_frame()
        self.view.set_status("Playing recorded performance")

    def _prepare_combined_audio(self, offset_ms: int) -> Optional[np.ndarray]:
        """Prepare a stereo mixed waveform of original audio plus the user's recording."""
        if self.model.audio_data is None or self.model.recorded_audio is None:
            return None
        sample_rate = self.model.sample_rate
        if sample_rate <= 0:
            return None

        recorded_audio = self.model.recorded_audio
        recorded_audio = self._resample_recording_if_needed(recorded_audio)
        recorded_audio = self._normalize_recording_volume(recorded_audio)

        start_sample = int(round(offset_ms * sample_rate / 1000.0))
        original_segment = self.model.audio_data[start_sample:]
        if original_segment.ndim == 1:
            original_segment = original_segment[:, None]

        recorded_segment = recorded_audio[start_sample:]
        if recorded_segment.ndim == 1:
            recorded_segment = recorded_segment[:, None]
        if recorded_segment.shape[1] == 1:
            recorded_segment = np.repeat(recorded_segment, 2, axis=1)
        elif recorded_segment.shape[1] > 2:
            recorded_segment = recorded_segment[:, :2]

        if recorded_segment.shape[0] < original_segment.shape[0]:
            padding = np.zeros(
                (original_segment.shape[0] - recorded_segment.shape[0], recorded_segment.shape[1]),
                dtype=recorded_segment.dtype,
            )
            recorded_segment = np.vstack((recorded_segment, padding))
        else:
            recorded_segment = recorded_segment[: original_segment.shape[0], :]

        original_float = original_segment.astype(np.float32, copy=False)
        recorded_float = recorded_segment.astype(np.float32, copy=False)
        mixed = np.clip(original_float * 0.35 + recorded_float * 0.9, -1.0, 1.0)
        return mixed

    def _normalize_recording_volume(self, recorded_audio: np.ndarray) -> np.ndarray:
        """Normalize the user's recorded audio to produce a more consistent voice level."""
        if recorded_audio.ndim == 1:
            recorded_audio = recorded_audio[:, None]
        recorded_float = recorded_audio.astype(np.float32, copy=False)
        rms = np.sqrt(np.mean(np.square(recorded_float), axis=0, keepdims=True))
        target_rms = 0.15
        gain = np.where(rms > 0, target_rms / np.maximum(rms, 1e-8), 1.0)
        normalized = recorded_float * gain
        return np.clip(normalized, -1.0, 1.0)

    def _resample_recording_if_needed(self, recorded_audio: np.ndarray) -> np.ndarray:
        """Resample the recorded audio to the current playback sample rate if necessary."""
        if self.model.recording_rate == self.model.sample_rate:
            return recorded_audio
        if recorded_audio.ndim == 1:
            recorded_audio = recorded_audio[:, None]
        source_rate = self.model.recording_rate
        target_rate = self.model.sample_rate
        if source_rate <= 0 or target_rate <= 0:
            return recorded_audio

        duration_seconds = recorded_audio.shape[0] / source_rate
        target_length = int(round(duration_seconds * target_rate))
        resampled = np.zeros((target_length, recorded_audio.shape[1]), dtype=np.float32)
        for channel in range(recorded_audio.shape[1]):
            source_times = np.linspace(0.0, duration_seconds, num=recorded_audio.shape[0], endpoint=False)
            target_times = np.linspace(0.0, duration_seconds, num=target_length, endpoint=False)
            resampled[:, channel] = np.interp(target_times, source_times, recorded_audio[:, channel])
        return resampled

    def _show_next_frame(self) -> None:
        """Fetch the next video frame synced to the current audio playback time."""
        if self.video_capture is None:
            return
        if self.play_start_time > 0:
            elapsed_ms = int((time.monotonic() - self.play_start_time) * 1000)
            desired_ms = self.seek_start_ms + elapsed_ms
        else:
            desired_ms = self.playback_position_ms
        if desired_ms >= self.video_length_ms:
            self.on_stop()
            return
        current_ms = int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC))
        if desired_ms > current_ms + self.video_frame_interval * 2:
            self.video_capture.set(cv2.CAP_PROP_POS_MSEC, float(desired_ms))
            success, frame = self.video_capture.read()
        else:
            success, frame = self.video_capture.read()
            while success and int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC)) < desired_ms - self.video_frame_interval:
                success, frame = self.video_capture.read()
        if not success:
            self.on_stop()
            return
        self.view.set_video_frame(frame)
        position_ms = int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC))
        self.view.update_progress(position_ms, self.video_length_ms)

    def update_ui(self) -> None:
        """Refresh the playback progress indicator while the media is active."""
        if not self.is_playing or self.video_capture is None:
            return
        position_ms = int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC))
        self.view.update_progress(position_ms, self.video_length_ms)


def main() -> None:
    """Application entry point for the karaoke app."""
    app = QApplication(sys.argv)
    model = KaraokeModel()
    view = KaraokeView(model)
    controller = KaraokeController(model, view)
    controller.load_songs()
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
