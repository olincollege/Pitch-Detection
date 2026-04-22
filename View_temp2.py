# from tkinter import ttk
import threading
import time
from pathlib import Path
import numpy as np
from scipy import signal as sg
import sounddevice as sd
import soundfile as sf
import random

# Get the absolute paths for project directories
SCRIPT_DIR = Path(__file__).parent.parent
SOUNDS_DIR = SCRIPT_DIR / "Sounds"
LYRICS_FILE = SCRIPT_DIR / "Figures" / "Assets" / "lyrics.txt"
SONG_FILE = SOUNDS_DIR / "NeverGonnaGiveYouUp.wav"

# Try to import PIL for background image
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
# View Begins Here:
class KaraokeView:
    """
    Handles the main viewing mechanism of the Karaoke machine.
    Console-based version that displays information in the terminal.
    """

    def __init__(self):
        """
        Initializes the console view
        """
        self.controller = None
        self.recording = False
        print("🎤 Karaoke App Initialized (Console Mode) 🎤")
        print("Song: Never Gonna Give You Up")
        print("Score: 0")

    def toggle_recording(self):
        """
        Sends a command to the controller to start/stop recording
        """
        if self.controller:
            self.controller.toggle_recording()

    def update_lyrics(self, text):
        """
        Updates the lyrics in the console
        """
        print(f"\n📝 Lyrics:\n{text}\n")

    def update_score(self, score):
        """
        Updates the score in the console
        """
        print(f"🎵 Current Score: {score}")

    def show_message(self, message):
        """
        Shows a message in the console
        """
        print(f"ℹ️  {message}")

    def get_user_input(self, prompt):
        """
        Gets user input from console
        """
        return input(prompt)


# Controller Begins Here:


class KaraokeController:
    """
    The controller recieves commands from the view and sends it to the model.
    It also retrieves information from the model and plays it, updating view accordingly.
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.recording = False
        self.view.controller = self
        self.view.update_lyrics(self.model.load_lyrics())

    def toggle_recording(self):
        """
        It turns on and off recording. Switches the recording/scoring loop.
        """
        if not self.recording:
            # Start recording
            self.recording = True
            self.view.recording = True
            self.view.record_btn.config(state=tk.DISABLED)
            
            # Start in a separate thread to avoid blocking UI
            record_thread = threading.Thread(target=self._do_recording)
            record_thread.daemon = True
            record_thread.start()
        else:
            # Stop recording
            self.recording = False
            self.view.recording = False
            sd.stop()
            self.view.record_btn.config(state=tk.NORMAL, text="Start Recording")
    
    def _do_recording(self):
        """
        Perform the actual recording in a background thread
        """
        try:
            # Volume controls for mixed playback (adjust these values: 0.0 to 1.0)
            song_volume = 0.3  # Reduce song volume
            rec_volume = 1.0   # Recording volume
            
            # Load song
            song_data, fs_song = sf.read(str(SONG_FILE), dtype='float32')
            
            # Convert stereo to mono if needed
            if song_data.ndim > 1:
                song_data = song_data[:, 0]
            
            # Resample if necessary
            if fs_song != self.model.fs:
                song_resampled = sg.resample(song_data, int(len(song_data) * self.model.fs / fs_song))
            else:
                song_resampled = song_data
            
            duration = len(song_resampled) / self.model.fs
            songaudio = song_resampled[:int(duration * self.model.fs)]
            
            print(f"Recording for {duration:.1f} seconds... Speak into your microphone while the song plays.")
            
            # Play the song and record simultaneously
            sd.play(songaudio, self.model.fs)
            recording = sd.rec(int(duration * self.model.fs), samplerate=self.model.fs, channels=1)
            sd.wait()  # Wait until recording finishes
            
            # Save recording
            SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
            sf.write(str(SOUNDS_DIR / 'recorded_audio.wav'), recording, self.model.fs)
            print("Recording saved as 'recorded_audio.wav'")
            
            # Mix audio
            rec_flat = recording.flatten()
            if len(rec_flat) > len(songaudio):
                rec_flat = rec_flat[:len(songaudio)]
            elif len(rec_flat) < len(songaudio):
                songaudio = songaudio[:len(rec_flat)]
            
            mixed_audio = (rec_volume * rec_flat + song_volume * songaudio) / 2
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(mixed_audio))
            if max_val > 1.0:
                mixed_audio = mixed_audio / max_val
            
            print("Playing mixed audio (recorded voice + backing track)...")
            sd.play(mixed_audio, self.model.fs)
            sd.wait()
            print("Playback complete")
            
            # Calculate and update score
            score = self.model.calculate_score()
            self.view.update_score(score)
            
        except Exception as e:
            print(f"Error during recording: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.recording = False
            self.view.recording = False
            self.view.record_btn.config(state=tk.NORMAL, text="Start Recording")

    def start_karaoke(self):
        """
        It starts playing the song by sending a command to the model
        """
        self.model.play_audio()
        # Placeholder scoring loop
        while self.recording:
            score = self.model.calculate_score()
            self.view.update_score(score)
            time.sleep(0.5)

    # Model Begins Here:





class KaraokeModel:
    """
    It plays the song and scores it based off the YIN algorithm.
    """

    def __init__(self):
        try:
            # Load song with correct path
            if not SONG_FILE.exists():
                print(f"Warning: Song file not found at {SONG_FILE}")
                # Try alternative path
                alt_path = SCRIPT_DIR / "Sounds" / "NeverGonnaGiveYouUp.wav"
                if alt_path.exists():
                    self.data, self.fs = sf.read(str(alt_path), dtype="float32")
                else:
                    raise FileNotFoundError(f"Song file not found at {SONG_FILE} or {alt_path}")
            else:
                self.data, self.fs = sf.read(str(SONG_FILE), dtype="float32")
            
            # Convert stereo → mono if needed
            if self.data.ndim > 1:
                self.data = self.data[:, 0]
            
            print(f"✓ Loaded song: {SONG_FILE}")
            print(f"✓ Sample rate: {self.fs} Hz")
            print(f"✓ Duration: {len(self.data) / self.fs:.2f} seconds")
            
        except Exception as e:
            print(f"Error loading song: {e}")
            # Create dummy data for testing
            self.fs = 44100
            self.data = np.zeros(self.fs * 2)  # 2 seconds of silence

    def play_audio(self):
        """
        Plays the preloaded audio using sounddevice
        """
        try:
            sd.play(self.data, self.fs)
        except Exception as e:
            print(f"Error playing audio: {e}")

    def stop_audio(self):
        """
        Stops audio playback
        """
        sd.stop()

    def load_lyrics(self):
        """
        Loads the lyrics
        """
        try:
            if not LYRICS_FILE.exists():
                print(f"Warning: Lyrics file not found at {LYRICS_FILE}")
                return "No lyrics file found. Add lyrics.txt to Figures/Assets/"
            
            with open(LYRICS_FILE, "r") as f:
                lyrics = f.read()
                print(f"✓ Loaded lyrics from {LYRICS_FILE}")
                return lyrics
        except Exception as e:
            print(f"Error loading lyrics: {e}")
            return f"Error loading lyrics: {str(e)}"

    def calculate_score(self):
        """
        Calculate the score based off the pitch differences.
        With the current implementation not being complete and
        using a random value from 50 to 100
        """
        return random.randint(50, 100)


# ============================================================================
# MAIN - Application Entry Point
# ============================================================================


if __name__ == "__main__":
    """
    Main entry point for the Karaoke application.
    
    Initializes the Model, View, and Controller in the MVC architecture
    and starts the tkinter event loop.
    """
    try:
        print("\n" + "="*60)
        print("🎤 Karaoke Application Starting 🎤")
        print("="*60)
        
        # Create model (loads audio and lyrics)
        print("\nLoading audio and lyrics...")
        model = KaraokeModel()
        
        # Create view (UI)
        print("Initializing UI...")
        view = KaraokeView()
        
        # Create controller (connects Model and View)
        print("Setting up controller...")
        controller = KaraokeController(model, view)
        
        # Start the application
        print("\n✓ Karaoke application ready!")
        print("="*60 + "\n")
        view.mainloop()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

