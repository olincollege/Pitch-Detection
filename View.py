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