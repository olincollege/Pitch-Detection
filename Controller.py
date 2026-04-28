# -*- coding: utf-8 -*-
"""
Karaoke app controller and application entrypoint.
"""
import sys
import time
from typing import Optional

import cv2
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from Model import KaraokeModel, AudioRecorder
from View import KaraokeView


class KaraokeController:
    """Controller that coordinates model state and view interactions."""

    def __init__(self, model: KaraokeModel, view: KaraokeView):
        """
        Summary:
            Initialize the karaoke controller with model and view.

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
        """
        Summary:
            Load the available songs into the view list.

        Returns:
            None
        """
        self.model.songs = self.model.list_songs()
        self.view.set_song_list(self.model.songs)
        if not self.model.songs:
            self.view.set_status('No songs found in the Figures folder')

    def on_song_selected(self, song_name: str) -> None:
        """
        Summary:
            Handle song selection from the view and reset active playback.

        Args:
            song_name (str): The selected song name.

        Returns:
            None
        """
        if self.is_playing or self.is_paused or self.is_recording:
            self.on_stop()
        if self.model.set_selected_song(song_name):
            self.view.load_video(str(self.model.selected_path))
            self.view.set_status(f'Selected: {song_name}')
            self.model.load_audio_track()
            self.playback_position_ms = 0
            self.view.clear_video()
        else:
            self.view.set_status('Unable to select song')

    def on_play(self) -> None:
        """
        Summary:
            Start playback, resume paused playback, or pause current playback.

        Returns:
            None
        """
        if self.is_playing and not self.is_paused:
            self.pause_playback()
            return
        if self.is_paused:
            self.resume_playback()
            return
        if self.model.selected_path is None:
            self.view.set_status('Select a song before pressing Play')
            return
        self.start_playback()

    def _open_video_capture(self, start_ms: int = 0) -> bool:
        """
        Summary:
            Open the OpenCV video capture and set the desired start position.

        Args:
            start_ms (int): Milliseconds offset to begin video playback.

        Returns:
            True if the video file opens successfully; otherwise False.
        """
        if self.model.selected_path is None:
            return False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self.video_capture = cv2.VideoCapture(str(self.model.selected_path))
        if not self.video_capture.isOpened():
            self.view.set_status('Unable to open video file')
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
        """
        Summary:
            Begin video playback and immediate audio output from the selected song.

        Returns:
            None
        """
        if not self.model.load_audio_track():
            self.view.set_status('Unable to load audio track')
            return
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.seek_start_ms = self.playback_position_ms
        self.is_playing = True
        self.is_paused = False
        self.view.play_button.setText('Pause')
        self.view.timer.start(100)
        try:
            start_sample = int(round(self.playback_position_ms * self.model.sample_rate / 1000.0))
            sd.play(self.model.audio_data[start_sample:], self.model.sample_rate)
        except Exception:
            self.view.set_status('Audio playback failed')
            return
        self.play_start_time = time.monotonic()
        self.video_timer.start(self.video_frame_interval)
        self._show_next_frame()
        self.view.set_status('Playing')

    def resume_playback(self) -> None:
        """
        Summary:
            Resume playback from the point where it was paused.

        Returns:
            None
        """
        if self.model.selected_path is None:
            self.view.set_status('Select a song before pressing Play')
            return
        if self.is_recording and self.record_paused:
            self.recorder.resume()
            self.record_paused = False
        self.start_playback()

    def pause_playback(self) -> None:
        """
        Summary:
            Pause the active playback session and preserve the current position.

        Returns:
            None
        """
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
        self.view.play_button.setText('Play')
        self.view.set_status('Paused')
        if self.is_recording and not self.record_paused:
            self.recorder.pause()
            self.record_paused = True

    def on_stop(self) -> None:
        """
        Summary:
            Stop all playback and recording activity and reset playback state.

        Returns:
            None
        """
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
        self.view.play_button.setText('Play')
        self.view.record_button.setText('Record')
        self.view.set_status('Ready')
        self.view.clear_video()

    def on_record(self) -> None:
        """
        Summary:
            Start or stop recording the user's voice while the song plays.

        Returns:
            None
        """
        if self.is_recording:
            self.on_stop()
            return
        if self.model.selected_path is None:
            self.view.set_status('Select a song before recording')
            return
        if not self.model.load_audio_track():
            self.view.set_status('Unable to load audio track')
            return
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.recorder.start()
        self.is_recording = True
        self.record_paused = False
        self.is_playing = True
        self.is_paused = False
        self.seek_start_ms = self.playback_position_ms
        self.view.record_button.setText('Stop Recording')
        self.view.play_button.setText('Pause')
        self.view.set_status('Recording...')
        self.view.timer.start(100)
        self.video_timer.start(self.video_frame_interval)
        try:
            start_sample = int(round(self.playback_position_ms * self.model.sample_rate / 1000.0))
            sd.play(self.model.audio_data[start_sample:], self.model.sample_rate)
        except Exception:
            self.view.set_status('Audio playback failed')
            return
        self.play_start_time = time.monotonic()
        self._show_next_frame()

    def _stop_recording(self) -> None:
        """
        Summary:
            Stop recording and save the captured audio to the model.

        Returns:
            None
        """
        recording = self.recorder.stop()
        self.model.save_recording(recording)
        self.is_recording = False
        self.record_paused = False
        self.view.record_button.setText('Record')
        self.view.set_status('Recording saved')

    def on_playback_recording(self) -> None:
        """
        Summary:
            Play the selected video together with the user's saved recording from the start.

        Returns:
            None
        """
        if not self.model.has_recording():
            self.view.set_status('No recording available')
            return
        if self.model.selected_path is None:
            self.view.set_status('Select a song before playback')
            return
        if self.is_playing or self.is_recording or self.is_paused:
            self.on_stop()
        self.view.clear_video()
        self.view.set_status('Select a song to start video')
        if not self.model.load_audio_track():
            self.view.set_status('Unable to load audio track')
            return
        self.playback_position_ms = 0
        if not self._open_video_capture(self.playback_position_ms):
            return
        self.seek_start_ms = self.playback_position_ms
        self.is_playing = True
        self.is_paused = False
        self.view.play_button.setText('Pause')
        self.view.timer.start(100)
        mixed_audio = self._prepare_combined_audio(self.playback_position_ms)
        if mixed_audio is None:
            self.view.set_status('Unable to play combined audio')
            return
        try:
            sd.play(mixed_audio, self.model.sample_rate)
        except Exception:
            self.view.set_status('Playback of recording failed')
            return
        self.play_start_time = time.monotonic()
        self.video_timer.start(self.video_frame_interval)
        self.view.update_progress(0, self.video_length_ms)
        self._show_next_frame()
        self.view.set_status('Playing recorded performance')

    def _prepare_combined_audio(self, offset_ms: int) -> Optional[np.ndarray]:
        """
        Summary:
            Prepare a stereo mixed waveform of original audio plus the user's recording.

        Args:
            offset_ms (int): The playback offset in milliseconds.

        Returns:
            The mixed stereo audio or None when mixing is not possible.
        """
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
        """
        Summary:
            Normalize the user's recorded audio to produce a more consistent voice level.

        Args:
            recorded_audio (np.ndarray): The recorded waveform.

        Returns:
            The normalized audio waveform.
        """
        if recorded_audio.ndim == 1:
            recorded_audio = recorded_audio[:, None]
        recorded_float = recorded_audio.astype(np.float32, copy=False)
        rms = np.sqrt(np.mean(np.square(recorded_float), axis=0, keepdims=True))
        target_rms = 0.15
        gain = np.where(rms > 0, target_rms / np.maximum(rms, 1e-8), 1.0)
        normalized = recorded_float * gain
        return np.clip(normalized, -1.0, 1.0)

    def _resample_recording_if_needed(self, recorded_audio: np.ndarray) -> np.ndarray:
        """
        Summary:
            Resample the recorded audio to the current playback sample rate if necessary.

        Args:
            recorded_audio (np.ndarray): The recorded waveform.

        Returns:
            The resampled audio waveform.
        """
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
        """
        Summary:
            Fetch the next video frame synced to the current audio playback time.

        Returns:
            None
        """
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
        """
        Summary:
            Refresh the playback progress indicator while media is active.

        Returns:
            None
        """
        if not self.is_playing or self.video_capture is None:
            return
        position_ms = int(self.video_capture.get(cv2.CAP_PROP_POS_MSEC))
        self.view.update_progress(position_ms, self.video_length_ms)


def main() -> None:
    """
    Summary:
        Application entry point for the karaoke app.

    Returns:
        None
    """
    app = QApplication(sys.argv)
    model = KaraokeModel()
    view = KaraokeView(model)
    controller = KaraokeController(model, view)
    controller.load_songs()
    view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()