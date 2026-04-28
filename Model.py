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
FIGURES_DIR = PROJECT_ROOT / "Pitch-Detection" / "New Figures"
RECORDING_FILE = PROJECT_ROOT / "recording.wav" 
SUPPORTED_EXTENSIONS = [".mp4"]

# KaraokeModel class starts here
class KaraokeModel:
    """Model that tracks song selection, audio data, and recorded vocals."""

    def __init__(self, figures_dir: Path = FIGURES_DIR):
        """
        Summary: 
            Initialize the karaoke model with the figures directory.

        Args:
            figures_dir (Path): The directory containing MP4 files. Defaults to FIGURES_DIR (Pitch-Detection/New Figures).

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
        """
        Summary: 
            Returns the list of available MP4 song files.

        Returns:
            A sorted list of MP4 filenames found in the Pitch-Detection/New Figures directory.
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
        """
        Summary:
        Select the named song if the file exists.

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
        """
        Summary:
            Extract the MP4 audio track using FFmpeg and cache it as stereo audio.
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
        """
        Summary:
            Save the recorded vocals to a WAV file and cache the data.

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
        """
        Summary:
            Return True when a recording is available.

        Returns:
            True if a recording exists; otherwise False.
        """
        return self.recorded_audio is not None and len(self.recorded_audio) > 0
