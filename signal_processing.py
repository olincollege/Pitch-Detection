"""
The goal of this algorithm is to find the pitch and sync it to a file.
"""

import numpy as np
import librosa
from librosa.sequence import dtw
import matplotlib.pyplot as plt
from scipy.signal import medfilt
from scipy.signal import butter, filtfilt


class File_processing:
    """
    File processing
    """

    def __init__(self, ref_file, user_file):
        self.ref_file = ref_file
        self.user_file = user_file
        self.ref_pitch = None
        self.user_pitch = None
        self.alignment_path = None

    def extract_pitch(self, audio_file):
        """
        It recieves the file name of the audio and returns a nparray of the pitches.
        This program ses a sample rate of 22050 and other defaults to Librosa's piptrack
        method. It has a frequency range of 60 to 1000, which is the human vocal range.

        Args:
            audio_file, a String representing the name of the audiofile

        Returns:
            pitch_track, a numpy array of the pitches in the track
        """

        audio, sample_rate = librosa.load(audio_file)
        f0 = librosa.yin(audio, sr=sample_rate, fmin=60.0, fmax=1000.0)
        return f0

    def process_files(self):
        """
        Processes the files for both the reference and the user
        """
        self.ref_pitch = self.extract_pitch(self.ref_file)
        self.user_pitch = self.extract_pitch(self.user_file)

    def align_tracks(self):
        """
        Ensures both the reference and user audio have equal frames.
        If the user or the reference has more frames than the other,
        the minimum frames is used to ensure consistency between both audios.
        """
        min_frames = min(len(self.ref_pitch), len(self.user_pitch))
        self.ref_pitch = self.ref_pitch[0:min_frames]
        self.user_pitch = self.user_pitch[0:min_frames]

    def hz_to_midi(self, f):
        return 12 * np.log2(f / 440) + 69

    # ---------------------------
    # Generous pitch scoring
    # ---------------------------
    def pitch_score_generous(self):
        scores = []

        for ref_p, user_p in zip(self.ref_pitch, self.user_pitch):
            if np.isnan(ref_p) or np.isnan(user_p):
                continue

            error = abs(self.hz_to_midi(ref_p) - self.hz_to_midi(user_p))

            # --- GENEROUS TOLERANCE MODEL ---
            if error < 1:
                score = 100  # basically perfect
            elif error < 3:
                score = 90  # good
            elif error < 5:
                score = 85  # great
            elif error < 12:
                score = 75  # very off
            else:
                score = 75  # very off

            scores.append(score)

        return float(np.mean(scores)) if len(scores) > 0 else 0

    # ---------------------------
    # 6. Final score
    # ---------------------------
    def final_score(self):
        pitch = self.pitch_score_generous()
        print("pitch", self.pitch_score_generous())
        final = pitch
        return final

    # ---------------------------
    # 7. Graphing function
    # ---------------------------
    def plot_results(self):
        # if self.alignment_path is None:
        #    raise ValueError("Run align_tracks() first.")
        """
        ref_aligned = []
        user_aligned = []
        frame_scores = []

        # cum_scores = []

        for i, j in self.alignment_path:
            ref_p = self.ref_pitch[i]
            user_p = self.user_pitch[j]

            ref_aligned.append(ref_p)
            user_aligned.append(user_p)

            # Compute per-frame pitch score
            if not np.isnan(ref_p) and not np.isnan(user_p):
                error = abs(self.hz_to_cents(ref_p) - self.hz_to_cents(user_p))
                score = np.exp(-error / 50) * 100
            else:
                score = 0

            frame_scores.append(score)

        ref_aligned = np.array(ref_aligned)
        user_aligned = np.array(user_aligned)
        frame_scores = np.array(frame_scores)
        time = np.arange(len(ref_aligned))
        """
        """
        # ---- Cumulative logic ----
        # Sliding window average
        cumulative = np.zeros_like(frame_scores)
        for i in range(len(frame_scores)):
            start = max(0, i)
            cumulative[i] = np.mean(frame_scores[start : i + 1])
        """

        time = np.arange(len(self.user_pitch)) * (265) / (len(self.user_pitch))
        # ---- Plot 1: Pitch comparison ----
        plt.figure()
        plt.plot(
            time, np.array(self.hz_to_midi(self.ref_pitch)), label="Reference Pitch"
        )
        plt.plot(time, np.array(self.hz_to_midi(self.user_pitch)), label="User Pitch")
        plt.title("Pitch Comparison Over Time")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Midi Score")
        plt.legend()
        plt.grid()
        plt.show()

        # ---- Plot 2: Score in frames ----
        # plt.figure()
        # plt.plot(time, frame_scores)
        # plt.title("Score Over Time")
        # plt.xlabel("Time (frames)")
        # plt.ylabel("Score (0-100)")
        # plt.grid()
        # plt.show()
        # reference           # user

        # print(len(user_aligned))


processor = File_processing(
    "I Can't Help Falling In Love With You - Elvis Presley.mp4", "Recording.wav"
)

processor = File_processing("PerfectVocals_2.wav", "Itim_Perfect.wav")

# processor = File_processing("Perfect_Vocals.wav", "PerfectVocals_2.wav")
processor.process_files()
processor.align_tracks()
scores = processor.final_score()
print(scores)
processor.plot_results()


# Observation, the song ends but the user is not singing.

# If a pause is less than 5 seconds, it does not count .
