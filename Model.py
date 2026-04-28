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
