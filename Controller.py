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