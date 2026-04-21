from time import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


# View Begins Here:
class KaraokeView(tk.Tk):
    """
    Handles the main viewing mechanism of the Karaoke machine.
    It should be able to start/end recordings, display the score,
    song lyrics, play the background song, and select the song.
    """

    def __init__(self):
        """
        Initializes the tkinter view and sets up the widgets.
        The dimension of the view is 800 x 600
        """
        super().__init__()
        self.title("Karaoke App")
        self.geometry("800x600")
        self.setup_background()
        self.create_widgets()

    def setup_background(self):
        """
        It should set the background to the image
        """
        image = Image.open("Figures1.jpg")
        image = image.resize((800, 600))
        self.bg_image = ImageTk.PhotoImage(image)

        self.bg_label = tk.Label(self, image=self.bg_image)
        self.bg_label.place(relwidth=1, relheight=1)

    def create_widgets(self):
        """
        Creates the following widgets:
        - Title
        - Song selection
        - Start/Stop button
        - Lyrics display
        - Score Label
        """
        # Title
        self.title = tk.Label(
            self, text="Karaoke App", font=("Papyrus", 24), bg="black", fg="white"
        )
        self.title.pack(pady=10)

        # Song selection (MVP = one song)
        self.song_label = tk.Label(
            self, text="Song: Never Gonna Give You Up", bg="black", fg="white"
        )
        self.song_label.pack()

        # Start/Stop button
        self.record_btn = ttk.Button(
            self, text="Start Recording", command=self.toggle_recording
        )
        self.record_btn.pack(pady=10)

        # Lyrics display
        self.lyrics_box = tk.Text(self, height=10, width=60)
        self.lyrics_box.pack(pady=10)

        # Score label
        self.score_label = tk.Label(
            self, text="Score: 0", font=("Arial", 16), bg="black", fg="white"
        )
        self.score_label.pack(pady=10)

    def toggle_recording(self):
        """
        Sends a command to the controller to stop recording
        """
        self.controller.toggle_recording()

    def update_lyrics(self, text):
        """
        Updates the lyrics in real time
        """
        self.lyrics_box.delete("1.0", tk.END)
        self.lyrics_box.insert(tk.END, text)

    def update_score(self, score):
        """
        Updates the score
        """
        self.score_label.config(text=f"Score: {score}")


# Controller Begins Here:
import threading


class KaraokeController:
    """
    The controller recieves commands from the view and sends it to the model.
    It also retrieves information from the model and plays it, updating view accordingly.
    """

    def __init__(self, model, view):

        self.model = model
        self.view = view
        self.recording = False

        self.view.update_lyrics(self.model.load_lyrics())

    def toggle_recording(self):
        """
        It turns on and off recording. Switches the recording/scoring loop.
        """
        if not self.recording:

            self.recording = True
            self.view.record_btn.config(text="Stop Recording")
        else:

            self.recording = False
            self.view.record_btn.config(text="Start Recording")
            self.model.stop_audio()
            # self.view.update_score(0)  # Reset score on stop

    def start_karaoke(self):
        """
        It starts playing the song by sending a command to the model
        """
        self.model.play_audio()
        # Placeholder scoring loop
        import time

        while self.recording:
            score = self.model.calculate_score()
            self.view.update_score(score)
            time.sleep(0.5)

    # Model Begins Here:


import sounddevice as sd
import soundfile as sf
import random


class KaraokeModel:
    """
    It plays the song and scores it based off the YIN algorithm.
    """

    def __init__(self):
        self.song_path = "NeverGonnaGiveYouUp.wav"
        self.lyrics_path = "lyrics.txt"
        self.data, self.fs = sf.read(self.song_path, dtype="float32")
        # Convert stereo → mono if needed
        if self.data.ndim > 1:
            self.data = self.data[:, 0]

    def play_audio(self):
        """
        Plays the preloaded audio using sounddevice
        """
        sd.play(self.data, self.fs)

    def stop_audio(self):
        """
        Stops audio playback
        """
        sd.stop()

    def load_lyrics(self):
        """
        Loads the lyrics
        """
        with open(self.lyrics_path, "r") as f:
            return f.read()

    def calculate_score(self):
        """
        Calculate the score based off the pitch differences.
        With the current implementation not being complete and
        using a random value from 50 to 100
        """
        return random.randint(50, 100)


model = KaraokeModel()
# Test lyrics loading
lyrics = model.load_lyrics()
print("Lyrics loaded:\n", lyrics[:100])  # print first 100 chars

# Test audio playback
print("Playing song...")
model.play_audio()  # did I import sounddevice as sd?

# Test scoring
print("Score:", model.calculate_score())

###################

model = KaraokeModel()

print("Lyrics loaded:\n", model.load_lyrics()[:100])

print("Playing song...")
model.play_audio()

print("Score:", model.calculate_score())

######## Testing Screen

# This is how you actually run the app
screen = KaraokeView()
screen.mainloop()
