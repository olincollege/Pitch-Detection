from time import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
# View Begins Here:
class KaraokeView(tk.Frame):
    def __init__(self, root, controller):
        super().__init__(root)
        self.controller = controller
        self.pack(fill="both", expand=True)

        self.setup_background()
        self.create_widgets()
    def setup_background(self):
        image = Image.open("Figures/timeSignal.png")
        image = image.resize((800, 600))
        self.bg_image = ImageTk.PhotoImage(image)

        self.bg_label = tk.Label(self, image=self.bg_image)
        self.bg_label.place(relwidth=1, relheight=1)

    def create_widgets(self):
        # Title
        self.title = tk.Label(self, text="Karaoke App",
                              font=("Papyrus", 24), bg="black", fg="white")
        self.title.pack(pady=10)

        # Song selection (MVP = one song)
        self.song_label = tk.Label(self, text="Song: Never Gonna Give You Up",
                                  bg="black", fg="white")
        self.song_label.pack()

        # Start/Stop button
        self.record_btn = ttk.Button(self, text="Start Recording",
                                    command=self.toggle_recording)
        self.record_btn.pack(pady=10)
        
        # Lyrics display
        self.lyrics_box = tk.Text(self, height=10, width=60)
        self.lyrics_box.pack(pady=10)

        # Score label
        self.score_label = tk.Label(self, text="Score: 0",
                                   font=("Arial", 16), bg="black", fg="white")
        self.score_label.pack(pady=10)

    def toggle_recording(self):
        self.controller.toggle_recording()
    def update_lyrics(self, text):
        self.lyrics_box.delete("1.0", tk.END)
        self.lyrics_box.insert(tk.END, text)

    def update_score(self, score):
        self.score_label.config(text=f"Score: {score}")


# Controller Begins Here:

import threading

class KaraokeController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.recording = False

        self.view.update_lyrics(self.model.load_lyrics())

    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.view.record_btn.config(text="Stop Recording")
        else:
            self.recording = False
            self.view.record_btn.config(text="Start Recording")
            self.model.stop_audio()
            #self.view.update_score(0)  # Reset score on stop
    def start_karaoke(self):
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
    def __init__(self):
        self.song_path = "Sounds/RickAstleyWAV.wav"
        self.lyrics_path = "Figures/Assets/lyrics.txt"
        self.data, self.fs = sf.read(self.song_path, dtype='float32')
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
        with open(self.lyrics_path, "r") as f:
            return f.read()

    def calculate_score(self):
        return random.randint(50, 100)                                                   
model = KaraokeModel()
# Test lyrics loading
lyrics = model.load_lyrics()
print("Lyrics loaded:\n", lyrics[:100])  # print first 100 chars

# Test audio playback
print("Playing song...")
model.play_audio() # did I import sounddevice as sd?

# Test scoring
print("Score:", model.calculate_score())

model = KaraokeModel()

print("Lyrics loaded:\n", model.load_lyrics()[:100])

print("Playing song...")
model.play_audio()

print("Score:", model.calculate_score())
