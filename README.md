# Pitch-Detecting Karaoke Machine
By Thanadetch (Detch) Mateedunsatits and Liam Bennicoff
## Description
It uses a pitch detection algorithm to score karaoke singing. It requires .wav or .mp4 files from the user, specifically covering the vocal tracks of the song to test (reference audio) and the user's singing (user audio). It will score them from 50 to 100, purely on pitch. It uses the MIDI scale and has two levels of sensitivity, with one meant for beginners and another for those who are confident at singing. The sensitivity of the model and scoring system can be changed in karaoke_scorer.py. It also has a GUI to browse all tracks loaded into the program, as well as built-in recording, scoring, MIDI score over time, and playback features. 

## Features
![](Example_Screen.jpg)
1. Play, to play the video file. 
2. Record, to play and record the video file.
3. Stop/Pause, to stop the video file. The button shows up as pause if the video is already being played.
4. Playback, to play back the user's singing overlayed on the musical back track.
5. Score, displays a score from 50 to 100 depending on how well you sung.
6. Waveform viewer, display a waveform of the user's singing as well as the vocal track.

## Installation Instructions
1. It is recommened to use Python 3.13.0 as that was the version the development team used
2. Download the files from the main project via the green "Code" button
3. Extract all from the .zip file
4. Download all require libraries via `pip install -r requirements.txt`
5. Check requirements are fufilled by heading over to the `tests` folders and running `import_check.py`
6. Run the program using `main.py` after fufilling the instructions below and populating the `Songs\Karaoke-Tracks\` and `Songs\Vocal-Tracks\`folder with the proper Songs to play.

## Getting Started and file requirements (PLEASE READ!)
![](Starting_Screen.jpg)

When starting your first run of the `main.py` you will encounter that there are no songs in the list. The user can add their own songs into the application through the `Songs` folder. The songs should be `.mp4` format for the system to work best. Non-mp4 files will not show up on the left tab. When sourcing for Karaoke and Vocal tracks, they both must be `.mp4`

1. Getting your first Karaoke Track. The user may find it helpful to head to websites like `https://media.ytmp3.gg/youtube-to-mp4-converter` to convert the song they want to mp4 and put it into the folder to get it started. The YouTube channel SingKing or other Karaoke song providers on the internet are good places to start.
2. Put the song into `Songs\Karaoke-Tracks\` and name it whatever the user may want to name it
3. Getting your first Vocal Track. Again, the user may want to use the method mentioned in step 1 to source the file. The best Vocal tracks can be found by using the keywords: "Vocal track" or "Acapella" along with the song name.
4. Put the song into `Songs\Vocal-Tracks\` and the name MUST be exactly the same as in Step #2
5. !VERY IMPORTANT! Mantain exactly the same file names between `Songs\Karaoke-Tracks\` and `Songs\Karaoke-Tracks\`
6. For instance, we want to sing Perfect by Ed Sherran and the file is `Perfect.mp4` the Karoke Track should be in`Songs\Karaoke-Tracks\Perfect.mp4` and the Vocal Track should be `Songs\Vocal-Tracks\Perfect.mp4`. These are different files as one is a karaoke cover and another is a vocal track; however, they MUST be named the same filename even if they are different files. The same filename is how the system maps each Karaoke track to each Vocal tracks. Proceed to step 7 when the user has made sure both files are identically named
7. Run `main.py` when ready. If the song is not playing, it is likely there is an issue on step 5 so please make sure BOTH files are named exactly the same and share the exact same file extension. 

## Recording your first recording and Your first Score
![](Example_Pitch.jpg)
1. Select a song and click the record button
2. Once it has finish, WAIT WAIT WAIT. The program will freeze on you as it tries to compute the extremely intensive probalistic YIN process to get the score. Be patient please! It may take over a minute at times. This is not a bug. Exercise patience please.
3. Click the waveform button if you want to see the waveform. The calculation used a probalistic YIN model which is far more resistant to spikes than the one shown on the graph but produces sparser data points; hence, we've used the YIN model to produce more useful visualization. Both models should produce similar results and it's possible to override the scoring into a YIN through the functions in `Model.py`

## Score Meaning
1. By default the system works with a highly generous scoring system.

| Sensitivity (1 Semitone/100 cents) | Score | Technical Interpretation | General Scoring
| :--- | :---: | ---: | ---: |
| 1 | 100 | Good singing, you're within a semi-tone | Fantastic! |
| 2 | 90 | Okay singing, you're within a tone | Great Singing! |
| 5 | 85 | Fine singing, you're within a 2.5 tones | Good Singing! |
| 12 | 75 | There was singing, you're within 6 tones | Good Attempt! |
| ~ | 50 | The minimum score | Missed! | 

2. The user may want to use a more sensitive scoring system if they're a good singer who wants a challenge. The user may change this by heading into `Model.py` finding the function `calculate_score(self, level=0)` and setting `level=1` instead.

| Sensitivity (1 Semitone/100 cents)| Score | Technical Interpretation | General Scoring
| :--- | :---: | ---: | ---: |
| 0.25 | 100 | You sung within 25 cents | Fantastic! In-tune! |
| 0.5 | 90 | You sung within 50 cents | Good try! Slighly off-tune! | 
| 1 | 85 | You sung within a semi-tone | Okay! Off tune! |
| 2 | 75 | You sung within a tone! | Bad! You sung out of tune! |
| ~ | 50 | The minimum score | Missed! |

3. For even greater fine_tuning, the user may want to head to `karaoke_scorer.py` and modify the `pitch_score()` function to change the threshold for scoring.

## Unit Testing
### Karaoke Scorer and Scoring system
- Download `itim_perfect.wav` (sample user audio) needed to test. It is located in the `tests` folder
- Find an acapella cover of Perfect by Ed Sheeran and convert it to a .wav file using the method mentioned above.
- Rename the file to `PerfectVocals.mp4`/.wav or adjust the filename in `karaoke_scorer_test.py` to align with whatever filename you chose
- Run the `karaoke_scorer_test.py` file
- To test out the system more, the user can find and record a variety of test files aganist a song's vocal reference files.
### Main MVC tests
- Located in the tests folder
- Adjust the filepath in the media_test files to adjust for the various songs the user wants to test out.

### Known issues
1. There seems to be strong ringing behavior when using the Olin laptop microphone specifically. It seems to be a recorder specific issue as the testing shows that a clear audio recording from another source could yield scores as high as 94. 