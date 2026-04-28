from signal_processing import PitchScoring

# Users should change the "user" section to test their attempt on the Song "Perfect"
# If the reference song and user section can both be swapped for any .wav file or .mp4 file

# reference             # user
processor = PitchScoring("PerfectVocals_2.wav", "Itim_Perfect.wav")
processor.process_files()
processor.align_tracks()
scores = processor.pitch_score(level=0)
print(scores)
processor.plot_results()