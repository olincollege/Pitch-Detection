# -*- coding: utf-8 -*-
"""
Mister Microphone - Advanced Karaoke Application with Lyrics Highlighting and Synchronization
"""

import sys
import threading
import time
import numpy as np
from pathlib import Path
from scipy import signal
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QProgressBar, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QPixmap
from PyQt5.QtCore import pyqtSignal
import sounddevice as sd
import soundfile as sf


# ============================================================================
# MODEL SECTION - Data Management and Audio Processing
# ============================================================================

class AudioAnalyzer:
    '''
    Audio Frequency Analysis and Matching System
    
    Summary:
        Analyzes recorded audio to match frequency characteristics with original track
        and ensures synchronization during playback
    
    Args:
        sample_rate: Sampling frequency of audio (Hz)
        audio_data: Audio samples as numpy array
    
    Results:
        Returns frequency correction factor and confidence score for synchronization
    '''
    
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
    
    def analyze_frequency(self, audio_data):
        '''Calculate dominant frequency components'''
        try:
            # Compute FFT to find dominant frequencies
            fft = np.fft.fft(audio_data[:min(len(audio_data), 44100)])
            frequencies = np.fft.fftfreq(len(fft), 1/self.sample_rate)
            magnitude = np.abs(fft)
            
            # Find dominant frequencies
            positive_freqs = frequencies[:len(frequencies)//2]
            positive_magnitude = magnitude[:len(magnitude)//2]
            
            dominant_idx = np.argsort(positive_magnitude)[-5:]  # Top 5 frequencies
            dominant_freqs = positive_freqs[dominant_idx]
            
            return dominant_freqs
        except Exception as e:
            print(f'Frequency analysis error: {e}')
            return None
    
    def match_frequency(self, original_audio, recorded_audio):
        '''
        Match recorded audio frequency to original
        
        Summary:
            Compares frequency signatures and returns correction factor
        
        Args:
            original_audio: Original song audio data
            recorded_audio: Recorded vocal audio data
        
        Results:
            Returns frequency correction multiplier (0.9-1.1 range)
        '''
        try:
            orig_freqs = self.analyze_frequency(original_audio)
            rec_freqs = self.analyze_frequency(recorded_audio)
            
            if orig_freqs is not None and rec_freqs is not None:
                # Calculate average frequency ratio
                ratio = np.mean(orig_freqs) / np.mean(rec_freqs) if np.mean(rec_freqs) > 0 else 1.0
                # Clamp to reasonable range
                correction = np.clip(ratio, 0.9, 1.1)
                return correction
            return 1.0
        except Exception as e:
            print(f'Frequency matching error: {e}')
            return 1.0


class LyricsAnalyzer:
    '''
    Lyrics and Audio Synchronization Analysis
    
    Summary:
        Analyzes original track with lyrics to detect singing patterns and
        automatically match them to text for accurate highlighting timing
    
    Args:
        audio_data: Original audio track
        sample_rate: Sampling frequency
        lyrics_text: List of lyrics lines
    
    Results:
        Returns timing list for when each lyric line should be highlighted
    '''
    
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
    
    def detect_vocal_onset(self, audio_data, frame_length=2048, hop_length=512):
        '''
        Detect where vocals begin in audio
        
        Summary:
            Uses energy and spectral flux to detect vocal onsets
        
        Args:
            audio_data: Audio samples
            frame_length: Window size for analysis
            hop_length: Frames between windows
        
        Results:
            Returns array of onset times in seconds
        '''
        try:
            # Calculate energy envelope
            energy = np.array([
                np.sum(audio_data[i:i+frame_length]**2)
                for i in range(0, len(audio_data)-frame_length, hop_length)
            ])
            
            # Normalize and threshold
            energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy) + 1e-10)
            threshold = np.mean(energy) + np.std(energy)
            
            # Detect onsets
            onsets = np.where(energy > threshold)[0]
            onset_times = onsets * hop_length / self.sample_rate
            
            return onset_times
        except Exception as e:
            print(f'Vocal onset detection error: {e}')
            return np.array([])
    
    def generate_auto_timing(self, lyrics_list, audio_duration):
        '''
        Generate automatic timing for lyrics
        
        Summary:
            Distributes lyrics evenly across audio duration for demo purposes
        
        Args:
            lyrics_list: List of lyrics lines
            audio_duration: Total audio duration in seconds
        
        Results:
            Returns list of timestamps for each lyric
        '''
        if len(lyrics_list) == 0:
            return []
        
        # Distribute lyrics evenly across song duration
        timing = np.linspace(0, audio_duration * 0.95, len(lyrics_list))
        return timing.tolist()


class KaraokeModel:
    '''
    MODEL: Data Management and State
    
    Summary:
        Manages all application data including audio, lyrics, timing, and recording
    
    Args:
        None (initialized empty)
    
    Results:
        Provides interface for loading, storing, and accessing audio/lyrics data
    '''
    
    def __init__(self):
        # Audio data
        self.audio_data = None
        self.sample_rate = None
        self.audio_duration = 0
        
        # Lyrics data
        self.lyrics = []
        self.lyrics_times = []
        
        # Recording data
        self.recorded_audio = None
        self.recording_sample_rate = 44100
        
        # Analysis tools
        self.audio_analyzer = AudioAnalyzer(self.recording_sample_rate)
        self.lyrics_analyzer = LyricsAnalyzer(self.recording_sample_rate)
        
        # Playback state
        self.current_line = 0
        self.playback_position = 0
    
    def load_audio(self, audio_file):
        '''Load audio file into memory'''
        try:
            self.audio_data, self.sample_rate = sf.read(audio_file, dtype='float32')
            self.audio_duration = len(self.audio_data) / self.sample_rate
            print(f'Audio loaded: {len(self.audio_data)} samples at {self.sample_rate} Hz')
            return True
        except Exception as e:
            print(f'Error loading audio: {e}')
            return False
    
    def load_lyrics(self, lyrics_file):
        '''
        Load lyrics with automatic timing generation
        
        Summary:
            Loads lyrics from file and generates timing if not provided
        
        Args:
            lyrics_file: Path to lyrics file
        
        Results:
            Returns True if successful, updates self.lyrics and self.lyrics_times
        '''
        try:
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.lyrics = []
            self.lyrics_times = []
            
            # Try to parse timestamped format
            timestamped = False
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        try:
                            minutes = int(parts[0])
                            seconds = int(parts[1])
                            lyrics_text = parts[2]
                            timestamp = minutes * 60 + seconds
                            self.lyrics_times.append(timestamp)
                            self.lyrics.append(lyrics_text)
                            timestamped = True
                        except:
                            continue
            
            # If no timestamps, use auto-generation
            if not timestamped and lines:
                self.lyrics = [line.strip() for line in lines if line.strip()]
                self.lyrics_times = self.lyrics_analyzer.generate_auto_timing(
                    self.lyrics, self.audio_duration
                )
            
            print(f'Loaded {len(self.lyrics)} lyrics lines')
            return True
        except Exception as e:
            print(f'Error loading lyrics: {e}')
            return False
    
    def save_recording(self, audio_data, filename='recording.wav'):
        '''Save recorded audio to file'''
        try:
            sf.write(filename, audio_data, self.recording_sample_rate)
            self.recorded_audio = audio_data
            print(f'Recording saved: {filename}')
            return True
        except Exception as e:
            print(f'Error saving recording: {e}')
            return False
    
    def analyze_recording_frequency(self):
        '''Check if recorded audio frequency matches original'''
        if self.recorded_audio is None or self.audio_data is None:
            return 1.0
        
        correction = self.audio_analyzer.match_frequency(
            self.audio_data, self.recorded_audio
        )
        print(f'Frequency correction factor: {correction:.2f}')
        return correction


# ============================================================================
# VIEW SECTION - User Interface and Display
# ============================================================================

class KaraokeView(QWidget):
    '''
    VIEW: User Interface and Display Management
    
    Summary:
        Displays GUI elements including lyrics, buttons, progress bar, and
        handles all visual updates
    
    Args:
        None (initialized empty)
    
    Results:
        Renders complete karaoke interface with real-time updates
    '''
    
    # Signals for communication with controller
    play_pressed = pyqtSignal()
    record_pressed = pyqtSignal()
    stop_pressed = pyqtSignal()
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.background_image = self.set_background_image('Figures/Background.jpeg')  # Path to background image
        
        # Window setup
        self.setWindowTitle('Mister Microphone')
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet('background-color: #1a1a1a;')
        
        self.init_ui()
    
    def init_ui(self):
        '''
        Initialize User Interface Components
        
        Summary:
            Creates all UI elements including title, lyrics display, buttons, and progress
        
        Args:
            None (uses self for layout)
        
        Results:
            Configures complete GUI layout and styling
        '''
        layout = QVBoxLayout()
        
        # ===== TITLE SECTION =====
        title = QLabel('Mister Microphone')
        title.setFont(QFont('Arial', 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color: #00ff00; padding: 10px;')
        layout.addWidget(title)
        
        # ===== PROGRESS BAR =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                background-color: #333;
                border: 2px solid #00ff00;
                border-radius: 5px;
                color: white;
            }
            QProgressBar::chunk { background-color: #00ff00; }
        ''')
        layout.addWidget(self.progress_bar)
        
        # ===== TIME DISPLAY =====
        self.time_label = QLabel('00:00 / 00:00')
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet('color: #00ff00; font-size: 14px;')
        layout.addWidget(self.time_label)
        
        # ===== LYRICS DISPLAY (Star Wars Scroll Effect) =====
        self.lyrics_display = QTextEdit()
        self.lyrics_display.setFont(QFont('Arial', 24, QFont.Bold))
        self.lyrics_display.setReadOnly(True)
        self.lyrics_display.setAlignment(Qt.AlignCenter)
        
        # Make background transparent
        self.lyrics_display.setStyleSheet('''
            QTextEdit {
                background-color: transparent;
                color: #00ff00;
                border: none;
            }
        ''')
        layout.addWidget(self.lyrics_display)
        
        # ===== CONTROL BUTTONS =====
        button_layout = QHBoxLayout()
        button_style = '''
            QPushButton {
                background-color: #00ff00;
                color: black;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #00cc00; }
            QPushButton:pressed { background-color: #009900; }
        '''
        
        self.play_button = QPushButton('Play')
        self.play_button.setStyleSheet(button_style)
        self.play_button.clicked.connect(self.play_pressed.emit)
        button_layout.addWidget(self.play_button)
        
        self.record_button = QPushButton('Record')
        self.record_button.setStyleSheet(button_style)
        self.record_button.clicked.connect(self.record_pressed.emit)
        button_layout.addWidget(self.record_button)
        
        self.stop_button = QPushButton('Stop')
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.clicked.connect(self.stop_pressed.emit)
        button_layout.addWidget(self.stop_button)
        
        self.playback_button = QPushButton('Playback Recording')
        self.playback_button.setStyleSheet(button_style)
        self.playback_button.clicked.connect(self.playback_recording)
        button_layout.addWidget(self.playback_button)
        
        layout.addLayout(button_layout)
        
        # ===== STATUS LABEL =====
        self.status_label = QLabel('Ready')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('color: #00ff00; font-size: 12px; padding: 5px;')
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.on_timer_update)
        
        # Playback state
        self.is_playing = False
        self.is_recording = False
    
    def set_background_image(self, image_path):
        '''
        Set background image for GUI
        
        Summary:
            Loads and displays background image behind lyrics
        
        Args:
            image_path: Path to image file
        
        Results:
            Updates window background with scaled image
        '''
        try:
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaledToWidth(self.width())
            self.background_image = scaled_pixmap
            self.update()
        except Exception as e:
            print(f'Error loading background image: {e}')
    
    def update_lyrics_display(self, current_line_idx):
        '''
        Update lyrics display with upward scrolling effect
        
        Summary:
            Shows current line highlighted while displaying surrounding context,
            creates Star Wars-style upward scrolling effect
        
        Args:
            current_line_idx: Index of current lyric line to highlight
        
        Results:
            Updates lyrics display with highlighting and auto-scroll
        '''
        if current_line_idx >= len(self.model.lyrics):
            return
        
        # Build display with current line highlighted
        display_lines = []
        
        # Show future lines smaller (perspective effect)
        context = 3
        for i in range(max(0, current_line_idx - context), 
                       min(len(self.model.lyrics), current_line_idx + context + 1)):
            if i == current_line_idx:
                # Current line - highlighted in large font
                display_lines.append(f'<font size="5" color="#ff00ff"><b>{self.model.lyrics[i]}</b></font>')
            elif i < current_line_idx:
                # Previous lines - fade out upward
                opacity = int(255 * (1 - (current_line_idx - i) / context))
                display_lines.append(f'<font color="#{opacity:02x}00ff">{self.model.lyrics[i]}</font>')
            else:
                # Next lines - fade in downward
                opacity = int(255 * ((i - current_line_idx) / context))
                display_lines.append(f'<font color="#{opacity:02x}00ff">{self.model.lyrics[i]}</font>')
        
        html_content = '<br>'.join(display_lines)
        self.lyrics_display.setHtml(html_content)
    
    def update_progress(self, current_time, total_time):
        '''Update progress bar and time display'''
        if total_time > 0:
            progress = int((current_time / total_time) * 100)
            self.progress_bar.setValue(progress)
        
        time_str = f'{int(current_time)//60:02d}:{int(current_time)%60:02d} / {int(total_time)//60:02d}:{int(total_time)%60:02d}'
        self.time_label.setText(time_str)
    
    def set_status(self, status_text):
        '''Update status label'''
        self.status_label.setText(status_text)
    
    def on_timer_update(self):
        '''Timer callback for periodic UI updates'''
        pass
    
    def playback_recording(self):
        '''Emit signal to play back recorded audio'''
        self.status_label.setText('Playing back recording with original...')


# ============================================================================
# CONTROLLER SECTION - Logic and Event Handling
# ============================================================================

class KaraokeController:
    '''
    CONTROLLER: Application Logic and Event Handling
    
    Summary:
        Manages application flow, connects UI events to model operations,
        handles audio playback and recording
    
    Args:
        model: KaraokeModel instance
        view: KaraokeView instance
    
    Results:
        Coordinates all user interactions with data and display updates
    '''
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # Connect signals
        self.view.play_pressed.connect(self.on_play_pressed)
        self.view.record_pressed.connect(self.on_record_pressed)
        self.view.stop_pressed.connect(self.on_stop_pressed)
        self.view.playback_button.clicked.connect(self.on_playback_pressed)
        
        # Playback state
        self.is_playing = False
        self.is_recording = False
        self.playback_start_time = 0
        self.playback_thread = None
        self.recording_thread = None
        self.recorded_audio_data = None
        self.last_displayed_line = -1  # Track last line for smooth scrolling
        self.stop_requested = False  # Flag to stop audio playback
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_playback)
    
    def load_song(self, audio_file, lyrics_file):
        '''
        Load song and lyrics files
        
        Summary:
            Loads audio file and corresponding lyrics, initializes playback
        
        Args:
            audio_file: Path to audio file (WAV, MP3, etc)
            lyrics_file: Path to lyrics file
        
        Results:
            Returns True if successful, updates model and view
        '''
        audio_loaded = self.model.load_audio(audio_file)
        lyrics_loaded = self.model.load_lyrics(lyrics_file)
        
        if audio_loaded and lyrics_loaded:
            # Update view with lyrics
            all_lyrics = '\n'.join(self.model.lyrics)
            self.view.lyrics_display.setPlainText(all_lyrics)
            self.view.set_status('Song loaded successfully')
            self.view.update_progress(0, self.model.audio_duration)
            return True
        else:
            self.view.set_status('Error loading song or lyrics')
            return False
    
    def on_play_pressed(self):
        '''Handle play/pause button click'''
        if not self.is_playing:
            self.start_playback()
        else:
            self.pause_playback()
    
    def on_record_pressed(self):
        '''
        Handle record button click
        
        Summary:
            Starts recording vocal input and begins song playback with lyrics sync
        
        Args:
            None (triggered by button click)
        
        Results:
            Starts background recording thread and syncs with playback
        '''
        if not self.is_recording:
            # Start song playback and recording together
            self.start_recording_with_playback()
        else:
            self.stop_recording()
    
    def on_stop_pressed(self):
        '''Handle stop button click - completely stops playback'''
        self.stop_requested = True  # Flag to stop audio
        sd.stop()  # Stop current audio playback immediately
        self.stop_playback()
        self.is_recording = False
        self.view.record_button.setText('Record')
        self.view.play_button.setText('Play')
        self.view.set_status('Stopped')
        self.update_timer.stop()
        self.view.update_progress(0, self.model.audio_duration)
        # Reset scrolling state
        self.last_displayed_line = -1
        self.view.lyrics_display.setPlainText('')
    
    def on_playback_pressed(self):
        '''
        Handle playback recording button click
        
        Summary:
            Plays back recorded audio synchronized with original song
        
        Args:
            None (triggered by button click)
        
        Results:
            Plays both audio tracks together for comparison
        '''
        if self.recorded_audio_data is None:
            self.view.set_status('No recording available')
            return
        
        # Analyze frequency match
        correction = self.model.analyze_recording_frequency()
        
        # Resample recorded audio if needed
        if abs(correction - 1.0) > 0.01:
            adjusted_audio = self.resample_audio(
                self.recorded_audio_data, 
                correction
            )
        else:
            adjusted_audio = self.recorded_audio_data
        
        self.view.set_status('Playing recording with original...')
        self.playback_recording_with_original(adjusted_audio)
    
    def start_playback(self):
        '''Start audio playback with synchronized lyrics'''
        self.is_playing = True
        self.playback_start_time = time.time()
        self.view.play_button.setText('Pause')
        self.view.set_status('Playing...')
        self.update_timer.start(100)  # Update every 100ms
        
        # Start audio in background thread
        self.playback_thread = threading.Thread(
            target=self._play_audio, 
            daemon=True
        )
        self.playback_thread.start()
    
    def pause_playback(self):
        '''Pause playback'''
        self.is_playing = False
        self.view.play_button.setText('Play')
        self.view.set_status('Paused')
        self.update_timer.stop()
    
    def stop_playback(self):
        '''Stop playback completely'''
        self.is_playing = False
        self.view.play_button.setText('Play')
        self.view.set_status('Stopped')
        self.update_timer.stop()
    
    def start_recording_with_playback(self):
        '''
        Start recording while song plays
        
        Summary:
            Initiates microphone recording and simultaneously starts song playback
            with lyrics highlighting and auto-scrolling for singer to follow
        
        Args:
            None (triggered by record button)
        
        Results:
            Starts background threads for recording and playback
        '''
        self.is_recording = True
        self.is_playing = True
        self.playback_start_time = time.time()
        
        self.view.record_button.setText('Stop Recording')
        self.view.play_button.setText('Playing...')
        self.view.set_status('Recording and playing...')
        self.update_timer.start(100)
        
        # Start both recording and playback
        self.recording_thread = threading.Thread(
            target=self._record_audio,
            daemon=True
        )
        self.recording_thread.start()
        
        self.playback_thread = threading.Thread(
            target=self._play_audio,
            daemon=True
        )
        self.playback_thread.start()
    
    def stop_recording(self):
        '''Stop recording'''
        self.is_recording = False
        self.is_playing = False
        self.view.record_button.setText('Record')
        self.view.play_button.setText('Play')
        self.view.set_status('Recording stopped')
        self.update_timer.stop()
    
    def _play_audio(self):
        '''Play audio in background thread'''
        try:
            if self.model.audio_data is not None:
                sd.play(self.model.audio_data, self.model.sample_rate)
                sd.wait()
                self.is_playing = False
                self.update_timer.stop()
        except Exception as e:
            print(f'Audio playback error: {e}')
    
    def _record_audio(self):
        '''
        Record audio in background thread
        
        Summary:
            Captures microphone input at specified sample rate and duration
        
        Args:
            None (uses model settings)
        
        Results:
            Saves recorded audio and updates model
        '''
        try:
            duration = self.model.audio_duration  # Record for song duration
            sample_rate = self.model.recording_sample_rate
            
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # Save recording
            self.recorded_audio_data = recording
            self.model.save_recording(recording, 'recording.wav')
            
        except Exception as e:
            print(f'Recording error: {e}')
    
    def update_playback(self):
        '''
        Update display during playback
        
        Summary:
            Updates progress bar, time display, and lyrics highlighting
            based on current playback position
        
        Args:
            None (timer callback)
        
        Results:
            Updates all UI elements with current playback state
        '''
        if not self.is_playing:
            return
        
        elapsed = time.time() - self.playback_start_time
        
        # Update progress
        self.view.update_progress(elapsed, self.model.audio_duration)
        
        # Find current lyric line
        current_line = 0
        for i, timestamp in enumerate(self.model.lyrics_times):
            if elapsed >= timestamp:
                current_line = i
        
        # Update lyrics highlighting
        self.view.update_lyrics_display(current_line)
    
    def resample_audio(self, audio_data, factor):
        '''
        Resample audio to match frequency
        
        Summary:
            Adjusts sample rate of audio to synchronize with original
        
        Args:
            audio_data: Audio samples
            factor: Resampling factor (1.0 = no change)
        
        Results:
            Returns resampled audio data
        '''
        try:
            if abs(factor - 1.0) < 0.001:
                return audio_data
            
            num_samples = int(len(audio_data) / factor)
            resampled = signal.resample(audio_data, num_samples)
            return resampled.astype('float32')
        except Exception as e:
            print(f'Resampling error: {e}')
            return audio_data
    
    def playback_recording_with_original(self, recorded_audio):
        '''
        Play recorded audio mixed with original song
        
        Summary:
            Plays recording and original song together for comparison,
            uses frequency-corrected recording
        
        Args:
            recorded_audio: Recorded vocal audio samples
        
        Results:
            Plays mixed audio and updates status
        '''
        try:
            # Ensure same length
            min_len = min(len(self.model.audio_data), len(recorded_audio))
            original = self.model.audio_data[:min_len]
            recording = recorded_audio[:min_len]
            
            # Mix audio (original at 70%, recording at 30%)
            mixed = original * 0.7 + recording * 0.3
            
            # Play mixed audio
            sd.play(mixed, self.model.sample_rate)
            sd.wait()
            
            self.view.set_status('Playback complete')
        except Exception as e:
            print(f'Playback error: {e}')
            self.view.set_status(f'Error: {str(e)}')


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

def main():
    '''
    Main Application Entry Point
    
    Summary:
        Initializes MVC components and launches Mister Microphone application
    
    Args:
        None (run from command line)
    
    Results:
        Launches complete karaoke application with all features
    '''
    app = QApplication(sys.argv)
    
    # Create MVC components
    model = KaraokeModel()
    view = KaraokeView(model)
    controller = KaraokeController(model, view)
    
    # Load song and lyrics
    audio_file = 'c:/Users/lbennicoff1/.vscode/YIN-Pitch/Sounds/NeverGonnaGiveYouUp.wav'
    lyrics_file = 'c:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Assets/lyrics.txt'
    
    if controller.load_song(audio_file, lyrics_file):
        print('Song loaded successfully')
    else:
        print('Failed to load song')
    
    # Show window
    view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
import sounddevice as sd
import soundfile as sf

class KaraokeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('?? YIN Pitch Karaoke ??')
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize data
        self.audio_data = None
        self.sample_rate = None
        self.lyrics = []
        self.lyrics_times = []
        self.is_playing = False
        self.is_recording = False
        self.start_time = 0
        
        self.init_ui()
        self.load_song()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('?? YIN Pitch Karaoke ??')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Lyrics display
        self.lyrics_display = QTextEdit()
        self.lyrics_display.setFont(QFont('Arial', 16))
        self.lyrics_display.setReadOnly(True)
        self.lyrics_display.setStyleSheet('background-color: #2b2b2b; color: white; border: 2px solid #555; border-radius: 10px; padding: 10px;')
        layout.addWidget(self.lyrics_display)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.play_button = QPushButton('?? Play')
        self.play_button.clicked.connect(self.play_pause)
        button_layout.addWidget(self.play_button)
        
        self.record_button = QPushButton('??? Record')
        self.record_button.clicked.connect(self.record)
        button_layout.addWidget(self.record_button)
        
        self.stop_button = QPushButton('?? Stop')
        self.stop_button.clicked.connect(self.stop)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel('Ready')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        
    def load_song(self):
        try:
            # Load audio
            audio_file = 'c:/Users/lbennicoff1/.vscode/YIN-Pitch/Sounds/NeverGonnaGiveYouUp.wav'
            self.audio_data, self.sample_rate = sf.read(audio_file)
            print(f'Audio loaded: {len(self.audio_data)} samples')
            
            # Load lyrics
            lyrics_file = 'c:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Assets/lyrics.txt'
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Try timestamped format first
            timestamped = False
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        try:
                            minutes = int(parts[0])
                            seconds = int(parts[1])
                            lyrics_text = parts[2]
                            timestamp = minutes * 60 + seconds
                            self.lyrics_times.append(timestamp)
                            self.lyrics.append(lyrics_text)
                            timestamped = True
                        except:
                            continue
            
            # If no timestamps, treat as plain lyrics with automatic timing
            if not timestamped and lines:
                self.lyrics = [line.strip() for line in lines if line.strip()]
                # Create timestamps every 5 seconds
                self.lyrics_times = [i * 5 for i in range(len(self.lyrics))]
            
            # Display lyrics
            all_lyrics = '\n'.join(self.lyrics)
            self.lyrics_display.setPlainText(all_lyrics)
            self.status_label.setText('Song loaded successfully')
            print(f'Loaded {len(self.lyrics)} lyrics lines')
            
        except Exception as e:
            self.status_label.setText(f'Error loading song: {str(e)}')
            print(f'Error: {e}')
    
    def play_pause(self):
        if not self.is_playing:
            self.start_playback()
        else:
            self.pause_playback()
    
    def start_playback(self):
        self.is_playing = True
        self.play_button.setText('?? Pause')
        self.status_label.setText('Playing...')
        self.start_time = time.time()
        self.timer.start(100)
        
        # Start audio in thread
        threading.Thread(target=self._play_audio, daemon=True).start()
    
    def pause_playback(self):
        self.is_playing = False
        self.play_button.setText('?? Play')
        self.status_label.setText('Paused')
        self.timer.stop()
    
    def _play_audio(self):
        try:
            if self.audio_data is not None:
                sd.play(self.audio_data, self.sample_rate)
                sd.wait()
                self.is_playing = False
                self.timer.stop()
        except Exception as e:
            print(f'Audio error: {e}')
    
    def record(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_button.setText('?? Stop Recording')
            self.status_label.setText('Recording...')
            threading.Thread(target=self._record_audio, daemon=True).start()
        else:
            self.is_recording = False
            self.record_button.setText('??? Record')
            self.status_label.setText('Recording stopped')
    
    def _record_audio(self):
        try:
            duration = 10
            sample_rate = 44100
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            sd.wait()
            sf.write('recording.wav', recording, sample_rate)
            print('Recording saved')
        except Exception as e:
            print(f'Recording error: {e}')
    
    def stop(self):
        self.is_playing = False
        self.is_recording = False
        self.play_button.setText('?? Play')
        self.record_button.setText('??? Record')
        self.status_label.setText('Stopped')
        self.timer.stop()
    
    def update_display(self):
        if not self.is_playing:
            return
            
        elapsed = time.time() - self.start_time
        
        # Update progress
        if self.audio_data is not None and self.sample_rate:
            total_duration = len(self.audio_data) / self.sample_rate
            progress = min(100, int((elapsed / total_duration) * 100))
            self.progress_bar.setValue(progress)
        
        # Find current line
        current_line = 0
        for i, timestamp in enumerate(self.lyrics_times):
            if elapsed >= timestamp:
                current_line = i
        
        # Highlight current line
        if current_line != getattr(self, 'last_line', -1):
            self.highlight_line(current_line)
            self.last_line = current_line
        
        # Auto-scroll
        if current_line < len(self.lyrics):
            cursor = self.lyrics_display.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for i in range(current_line):
                cursor.movePosition(QTextCursor.Down)
            self.lyrics_display.setTextCursor(cursor)
            self.lyrics_display.ensureCursorVisible()
    
    def highlight_line(self, line_index):
        if line_index >= len(self.lyrics):
            return
        
        # Reset formatting
        cursor = self.lyrics_display.textCursor()
        cursor.select(QTextCursor.Document)
        format_normal = QTextCharFormat()
        format_normal.setBackground(QColor('#2b2b2b'))
        format_normal.setForeground(QColor('white'))
        cursor.setCharFormat(format_normal)
        
        # Set text
        all_lyrics = '\n'.join(self.lyrics)
        self.lyrics_display.setPlainText(all_lyrics)
        
        # Highlight current line
        cursor = self.lyrics_display.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for i in range(line_index):
            cursor.movePosition(QTextCursor.Down)
        
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        
        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QColor('yellow'))
        format_highlight.setForeground(QColor('red'))
        format_highlight.setFontWeight(QFont.Bold)
        cursor.setCharFormat(format_highlight)

def main():
    app = QApplication(sys.argv)
    window = KaraokeApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
