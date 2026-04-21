import cv2
import matplotlib
import matplotlib.pyplot as plt
import scipy.io.wavfile as wav
import numpy as np
import pyaudio
import wave

matplotlib.use("Qt5Agg")  # Use non-interactive backend


class file_processesing:

    def __init__(self, path):
        # WAV file
        self.signal = path
        self.audio_frames = []
        self.sampling_rate = 0

    def process_audio(self):
        """
        It processes the audio into a series of audioframes.
        """
        # Scans through the .wav file in read only mode
        with wave.open(self.signal, "rb") as f:
            audio_channel = f.getnchannels()  # 1 represents mono, 2 represents stereo
            sample_width = f.getsampwidth()
            self.sample_rate = f.getframerate()
            raw_bytes = f.readframes(f.getnframes())

        # convert into numpy array
        signal = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)

        if audio_channel == 2:
            # in case it is stereo (L/R) sounds, turn it into a mono
            signal = signal.reshape(-1, 2)
            signal = (signal[:, 0] + signal[:, 1]) / 2

        # Normalise to [-1.0, 1.0]
        signal = signal / 32768.0

        sample_duration = 0.05  # 50 ms worth of samples
        frame_size = int(self.sample_rate * sample_duration)
        hop_size = frame_size // 2  # 50% overlap;

        frames = []
        for start in range(0, len(signal) - frame_size, hop_size):
            frame = signal[start : start + frame_size]
            frames.append(frame)

        frames = np.array(frames)
        window = np.hanning(frame_size)
        windowed_frames = np.zeros_like(frames)

        for i in range(len(frames)):
            windowed_frames[i] = frames[i] * window

        self.audio_frames = windowed_frames

        # print out statements for debugging
        print(f"Sample rate  : {self.sample_rate} Hz")
        print(f"Frame size   : {frame_size} samples")
        print(f"Num frames   : {len(windowed_frames)}")
        pass

    def auto_correlation(self):
        """
        Applies the autocorrelation algothrim on a signal.
        """
        all_corrected_frames = np.zeros(
            (len(self.audio_frames), self.audio_frames.shape[1])
        )

        for i in range(len(self.audio_frames)):
            current_frame = self.audio_frames[i]
            corrected_frame = np.correlate(current_frame, current_frame, mode="full")
            corrected_frame = corrected_frame[len(current_frame) - 1 :]
            # Normalise so zero-lag = 1.0
            if corrected_frame[0] > 0:
                corrected_frame = corrected_frame / corrected_frame[0]

            all_corrected_frames[i] = corrected_frame

        return all_corrected_frames

    def find_pitch(self):
        """
        Finds the pitch of the audio between the ranges of [50 , 1000] which represent the typical range
        of songs.
        """
        min_pitch = 50
        max_pitch = 1000
        min_lag = int(self.sample_rate / max_pitch)
        max_lag = int(self.sample_rate / min_pitch)
        pitch_guess = []
        all_corrected_frames = self.auto_correlation()

        for i in range(len(all_corrected_frames)):
            frame = all_corrected_frames[i]

            # Search only within the valid lag range
            search_region = frame[min_lag : max_lag + 1]

            # Find the lag with the highest ACF value in the search region
            peak_offset = np.argmax(search_region)
            peak_lag = peak_offset + min_lag  # offset back to absolute lag index
            peak_value = frame[peak_lag]

            # Convert lag to frequency
            f0 = self.sample_rate / peak_lag

            pitch_guess.append((f0, peak_value))

        for i, (f0, strength) in enumerate(pitch_guess[:]):
            print(f"Frame {i}: {f0:.1f} Hz  (ACF peak = {strength:.3f})")

        return len(pitch_guess)

    def difference_function(self, frame):
        n = len(frame)
        df = np.zeros(n)
        df[0] = 0  # zero-lag difference is always 0 by definition
        for lag in range(1, n):
            diff = frame[: n - lag] - frame[lag:]
            df[lag] = np.sum(diff**2)
        return df

    def cmndf(self, df):
        n = len(df)
        cmn = np.zeros(n)
        cmn[0] = 1
        running_sum = 0
        for lag in range(1, n):
            running_sum += df[lag]
            if running_sum == 0:
                cmn[lag] = 1  # silent frame — treat as unvoiced
            else:
                cmn[lag] = df[lag] / (running_sum / lag)
        return cmn

    def find_dip(self, cmn, min_lag, max_lag, threshold):
        # Walk through the search range and return the first lag that dips
        # below the threshold and is a local minimum
        for lag in range(min_lag, min(max_lag, len(cmn) - 1)):
            if cmn[lag] < threshold:
                # Refine: keep going while still descending
                while lag + 1 < max_lag and cmn[lag + 1] < cmn[lag]:
                    lag += 1
                return lag, cmn[lag]
        # No dip found — fall back to the global minimum in the search range
        search = cmn[min_lag : max_lag + 1]
        best_offset = int(np.argmin(search))
        best_lag = best_offset + min_lag
        return best_lag, cmn[best_lag]

    def signal_decomposition(self):
        """
        FFT
        STFT/Spectrogram; Some library
        MFCC
        Bandpass Filter
        Decompose signals into fundamental frequencies
        Plot_signal or To_image
        # uses matplot.pyplot() to plot the signals for debugging purposes
        Save this image to be used in debugging
        """
        pass

    def refine_lag(self, cmn, lag):
        # Parabolic interpolation for sub-sample accuracy (same as ACF version)
        if lag <= 0 or lag >= len(cmn) - 1:
            return float(lag)
        y0, y1, y2 = cmn[lag - 1], cmn[lag], cmn[lag + 1]
        denom = 2 * (2 * y1 - y0 - y2)
        if denom == 0:
            return float(lag)
        return lag + (y0 - y2) / denom

    def YIN_Algothrim(self):
        pitch_track = []
        min_pitch = 50
        max_pitch = 1000
        min_lag = int(self.sample_rate / max_pitch)
        max_lag = int(self.sample_rate / min_pitch)
        YIN_THRESHOLD = 0.4
        for i in range(len(self.audio_frames)):
            frame = self.audio_frames[i]

            df = self.difference_function(frame)
            cmn = self.cmndf(df)

            lag, dip_value = self.find_dip(cmn, min_lag, max_lag, YIN_THRESHOLD)
            refined = self.refine_lag(cmn, lag)
            f0 = self.sample_rate / refined

            # Voiced if the dip is below threshold (inverse of ACF — lower is better)
            if dip_value < YIN_THRESHOLD:
                pitch_track.append(f0)
            else:
                pitch_track.append(None)

        voiced = [f for f in pitch_track if f is not None]
        print(f"Total frames   : {len(pitch_track)}")
        print(f"Voiced frames  : {len(voiced)}")
        if voiced:
            print(f"Pitch range    : {min(voiced):.1f} – {max(voiced):.1f} Hz")

        return "processed"

    def plotter(self):
        pass

Process1 = file_processesing("NeverGonnaGiveYouUp.wav")
Process1.process_audio()
# print(Process1.auto_correlation())
# print(Process1.find_pitch())
print(Process1.YIN_Algothrim())

print("processed")
