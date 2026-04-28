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