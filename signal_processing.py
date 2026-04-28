import numpy as np
import librosa
import matplotlib.pyplot as plt


class PitchScoring:
    """
    Represents the pitch scoring system.

    Attributes:
        ref_file, a String representing the filepath to the vocal version of the song
        user_file, a String representing the filepath to the user's recording, which should only be their vocal singing
        ref_pitch, a initialized as none but will hold a numpy float array of reference pitches
        user_pitch, a initialized as none but will hold a numpy float array of user pitches
    """

    def __init__(self, ref_file, user_file):
        self.ref_file = ref_file
        self.user_file = user_file
        self.ref_pitch = None
        self.user_pitch = None

    def extract_pitch(self, audio_file, algorithm_type="pYIN", sensitivity=0.1):
        """
        It recieves the file name of the audio and returns a nparray of the pitches.
        It has a frequency range of 60 to 1000, which is the human vocal range.
        It uses a default threshold to identifying singing moments at 0.1 for voice probability.
        By default it implments the probalistic yin algorithm to detect pitch. This method is highly
        resistant to octave error making it ideal for extracting karaoke singing.
        YIN algorithm is similar but inferior in terms of extracting the right pitches 
        at the right moment, but much better for visualization, so both are implemented.

        Args:
            audio_file, a String representing the name of the audiofile
            algorithm_type, a String representing the algorithm we run to exact audio.
                            By default it is set to pYIN, but it also possible to set to the 
                            YIN algorithm (YIN). 
            sensitivity, an float representing the threshold sensitivity of the yin() and 
                        pyin() algorithm by default this value is set to 0.1

        Returns:
            pitch_track, a numpy array of the pitches in the track
        """
        audio, sample_rate = librosa.load(audio_file)
        if algorithm_type == "YIN":
            pitch_track = librosa.yin(y=audio, sr=sample_rate, fmin=60.0, fmax=1000.0, trough_threshold = sensitivity)
        if algorithm_type == "pYIN":
            pitch_track, voiced_flag, voiced_probs = librosa.pyin(
                y=audio, sr=sample_rate, fmin=60.0, fmax=1000.0
            )
            pitch_track[~voiced_flag] = np.nan
            pitch_track[voiced_probs < sensitivity] = np.nan

        return pitch_track

    def process_files(self, algorithm_type="pYIN"):
        """
        Processes the files for both the reference and the user and sets
        the pitches to the files.
        
        Args:
            algorithm_type, a String representing the algorithm we run to exact audio.
                            By default it is set to pYIN, but it also possible to set to the 
                            YIN algorithm (YIN). 
        """
        self.ref_pitch = self.extract_pitch(self.ref_file, algorithm_type)
        self.user_pitch = self.extract_pitch(self.user_file, algorithm_type)

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
        """
        It takes in a frequency and returns the midi score for that frequency.
        A midi score is a semitone unit of measurement with A4 (440 Hz) equalling
        69 midi score as a standard and following an equation for the rest.

        Args:
            f, a np array of floats representing the frequency

        Returns:
            a numpy array of floats representing the midi score.
        """
        return 12 * np.log2(f / 440) + 69

    def pitch_score(self, level=0):
        """
        A pitch based scoring system where there is two sensitivies for two levels of users.
        The easy level allows for 1, 2, 5, 12 MIDI-score as error ranges for score deductions.
        This is very generous and meant to exist for beginner karaoke users.
        The hard level allows for 0.25, 0.5, 1, 2 MIDI-score as error ranges, which are meant for
        quarter, half, a full-semitone, or two semitones or errors. This is meant for very confident
        singers in their pitch.

        Args:
            level, an integer 0 or 1, which represents the sensitivity of the scoring system
                and harshness of the program. With 0 being easy and 1 being for expert singers.
                By default is is 0, which is for easy.

        Returns:
            A float representing the mean score within the audioframe
        """
        scores = []  # pylint: disable=redefined-outer-name
        sensitivity_hard = [0.25, 0.5, 1, 2]
        sensitivity_easy = [1, 2, 5, 12]
        sensitivity_level = [sensitivity_easy, sensitivity_hard]
        for i, reference_pitch in enumerate(self.ref_pitch):
            user_pitch = self.user_pitch[i]
            if np.isnan(reference_pitch) or np.isnan(user_pitch):
                continue
            error = abs(self.hz_to_midi(reference_pitch) - self.hz_to_midi(user_pitch))
            if error < sensitivity_level[level][0]:
                score = 100  # basically perfect
            elif error < sensitivity_level[level][1]:
                score = 90  # great
            elif error < sensitivity_level[level][2]:
                score = 85  # good
            elif error < sensitivity_level[level][3]:
                score = 75  # solid
            else:
                score = 50  # off
            scores.append(score)
        return float(np.mean(scores))

    def plot_results(self):
        """
        Creates a plot of midi-score, time (in seconds) graph of the singer using the YIN algorithm.
        """
        duration = librosa.get_duration(path=self.user_file)
        self.process_files("YIN")
        self.align_tracks()

        time = np.arange(len(self.user_pitch)) * (duration) / (len(self.user_pitch))
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
