# -*- coding: utf-8 -*-
"""
Karaoke app view layer for song selection, video display, and playback controls.
"""
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QListWidget, QPushButton, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget


class KaraokeView(QWidget):
    """View layer that displays the song list, video widget, and player controls."""

    play_pressed = pyqtSignal()
    record_pressed = pyqtSignal()
    stop_pressed = pyqtSignal()
    playback_pressed = pyqtSignal()
    song_selected = pyqtSignal(str)

    def __init__(self, model) -> None:
        """
        Summary:
            Initialize the karaoke view with the model.

        Args:
            model: The model instance for the view.

        Returns:
            None
        """
        super().__init__()
        self.model = model
        self.setWindowTitle('Mister Microphone')
        self.setGeometry(100, 100, 1200, 900)
        self.video_label = QLabel('Select a song to load video')
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet('background-color: black; color: white;')
        self._build_ui()
        self.timer = QTimer(self)

    def _build_ui(self) -> None:
        """
        Summary:
            Create the main user interface widgets.

        Returns:
            None
        """
        self.song_list = QListWidget()
        self.song_list.currentItemChanged.connect(self._on_song_selection)

        heading = QLabel('Choose a song from the list and press Play')
        heading.setFont(QFont('Arial', 20, QFont.Bold))
        heading.setAlignment(Qt.AlignCenter)

        self.play_button = QPushButton('Play')
        self.record_button = QPushButton('Record')
        self.stop_button = QPushButton('Stop')
        self.playback_button = QPushButton('Playback Recording')

        self.play_button.clicked.connect(self.play_pressed.emit)
        self.record_button.clicked.connect(self.record_pressed.emit)
        self.stop_button.clicked.connect(self.stop_pressed.emit)
        self.playback_button.clicked.connect(self.playback_pressed.emit)

        control_layout = QHBoxLayout()
        for button in [self.play_button, self.record_button, self.stop_button, self.playback_button]:
            button.setMinimumHeight(50)
            control_layout.addWidget(button)

        self.status_label = QLabel('Ready')
        self.status_label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label)

        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel('Available Songs'))
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
        """
        Summary:
            Handle song selection from the view.

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
        """
        Summary:
            Populate the song list with available MP4 titles.

        Args:
            songs (List[str]): List of song filenames.

        Returns:
            None
        """
        self.song_list.clear()
        for song in songs:
            self.song_list.addItem(song)

    def get_selected_song_name(self) -> str:
        """
        Summary:
            Return the currently selected song title.

        Returns:
            The selected song name or empty string if none.
        """
        item = self.song_list.currentItem()
        return item.text() if item is not None else ''

    def set_status(self, text: str) -> None:
        """
        Summary:
            Update the status label text.

        Args:
            text (str): The status text to display.

        Returns:
            None
        """
        self.status_label.setText(text)

    def load_video(self, path: str) -> None:
        """
        Summary:
            Show a placeholder for the selected video file.

        Args:
            path (str): The path to the video file.

        Returns:
            None
        """
        self.video_label.setText(f'Loaded: {Path(path).name}')
        self.video_label.setStyleSheet('background-color: black; color: white;')

    def set_video_frame(self, frame: np.ndarray) -> None:
        """
        Summary:
            Render a video frame into the video display widget.

        Args:
            frame (np.ndarray): The video frame as a numpy array.

        Returns:
            None
        """
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
        """
        Summary:
            Clear the video display and show the default placeholder.

        Returns:
            None
        """
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText('Select a song to load video')
        self.video_label.setStyleSheet('background-color: black; color: white;')

    def update_progress(self, position_ms: int, duration_ms: int) -> None:
        """
        Summary:
            Update the progress bar using media position and duration.

        Args:
            position_ms (int): Current position in milliseconds.
            duration_ms (int): Total duration in milliseconds.

        Returns:
            None
        """
        if duration_ms <= 0:
            return
        ratio = min(max(position_ms / duration_ms, 0.0), 1.0)
        self.progress.setValue(int(ratio * 100))
        current_seconds = position_ms // 1000
        duration_seconds = duration_ms // 1000
        self.status_label.setText(
            f"{current_seconds // 60:02d}:{current_seconds % 60:02d} / {duration_seconds // 60:02d}:{duration_seconds % 60:02d}"
        )