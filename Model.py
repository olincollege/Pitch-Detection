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
