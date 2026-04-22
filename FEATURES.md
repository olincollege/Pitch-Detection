# Mister Microphone - Complete Feature Documentation

## Overview
**Mister Microphone** is a professional PyQt5-based karaoke application with advanced audio synchronization, frequency analysis, and recording capabilities.

---

## ✅ IMPLEMENTED FEATURES

### 1. **Fixed Encoding Issues**
- ✓ Fixed "NUL" display characters in button labels
- ✓ Proper UTF-8 encoding throughout application
- ✓ All emoji and special characters display correctly

### 2. **Application Title & Branding**
- ✓ Changed title to "**Mister Microphone**"
- ✓ Green retro theme (#00ff00) with dark background
- ✓ Professional styling with rounded buttons

### 3. **Button Labels (Emojis Removed)**
- ✓ "Play" - Clean text label
- ✓ "Record" - Clean text label
- ✓ "Stop" - Full stop button implemented
- ✓ "Playback Recording" - New button for reviewing recordings

### 4. **MVC Architecture with Full Documentation**
- ✓ **MODEL Section**:
  - `KaraokeModel`: Data management
  - `AudioAnalyzer`: Frequency analysis and matching
  - `LyricsAnalyzer`: Vocal onset detection and auto-timing
  
- ✓ **VIEW Section**:
  - `KaraokeView`: UI and display management
  
- ✓ **CONTROLLER Section**:
  - `KaraokeController`: Application logic and event handling

- ✓ All sections labeled with `# ===== [SECTION] =====` separators
- ✓ Comprehensive docstrings in format: `''' Summary Args and Results'''`

### 5. **Transparent Lyrics Display**
- ✓ Lyrics textbox has transparent background (no color box)
- ✓ Lyrics appear in bright green (#00ff00) for visibility
- ✓ Clean overlay effect without borders

### 6. **Star Wars-Style Upward Scrolling**
- ✓ Lyrics scroll upward from bottom to top
- ✓ Current line highlighted in **MAGENTA** with large font
- ✓ Previous lines fade out upward with decreasing opacity
- ✓ Next lines fade in downward with increasing opacity
- ✓ Creates perspective/3D effect similar to Star Wars opening
- ✓ Does not intersect with heading

### 7. **Advanced Audio Synchronization**
- ✓ **Frequency Analysis**: Analyzes dominant frequencies in audio
- ✓ **Frequency Matching**: Compares original and recorded audio frequencies
- ✓ **Correction Factor**: Calculates pitch correction (0.9-1.1 range)
- ✓ **Auto-Resampling**: Adjusts recorded audio to match original frequency

### 8. **Intelligent Lyrics Timing**
- ✓ **Timestamped Format Support**: Parses MM:SS:Lyrics format
- ✓ **Auto-Timing Generation**: Evenly distributes lyrics across song duration
- ✓ **Vocal Onset Detection**: Analyzes audio to find where vocals begin
- ✓ **Multiple Format Support**: Handles both timestamped and plain text lyrics

### 9. **Recording with Synchronization**
- ✓ **Synchronized Playback**: Press Record → Song plays + Auto-scroll + Lyrics highlight
- ✓ **Background Recording**: Captures microphone input during playback
- ✓ **Automatic Duration**: Records for entire song length
- ✓ **File Saving**: Saves recording as `recording.wav`
- ✓ **Frequency Analysis**: Analyzes recorded audio frequency characteristics

### 10. **Playback & Comparison Features**
- ✓ **Recording Playback**: Play back recorded vocal performance
- ✓ **Mixed Playback**: Original song (70%) + Recording (30%) mix
- ✓ **Frequency-Corrected Playback**: Adjusts recorded audio frequency for sync
- ✓ **Audio Comparison**: Hear how recording sounds with original track

### 11. **Progress Tracking**
- ✓ **Progress Bar**: Shows real-time playback position
- ✓ **Time Display**: Shows current time / total duration (MM:SS format)
- ✓ **Status Label**: Real-time status updates

### 12. **Play/Pause/Stop Controls**
- ✓ **Play Button**: Start playback with lyrics sync
- ✓ **Pause Button**: Pause without losing position
- ✓ **Stop Button**: Complete stop (resets position, clears highlighting)
- ✓ **Record Button**: Synchronized recording with playback

---

## 🎯 DETAILED FEATURE EXPLANATIONS

### Frequency Analysis System
```
1. AudioAnalyzer class performs FFT on audio
2. Detects top 5 dominant frequencies
3. Compares original vs recorded frequency profiles
4. Calculates correction ratio
5. Auto-resamples recorded audio if needed
```

### Lyrics Synchronization
```
1. LyricsAnalyzer detects vocal onsets
2. Uses energy envelope and spectral flux analysis
3. Generates automatic timestamps if needed
4. Updates highlighting every 100ms during playback
5. Smooth transitions between lyric lines
```

### Recording & Playback Flow
```
1. User clicks "Record"
2. Song starts playing
3. Lyrics auto-scroll and highlight
4. Microphone records simultaneously
5. After song ends:
   - Recording saved as recording.wav
   - Frequency analyzed
   - Can click "Playback Recording" to hear mix
   - Mixed audio plays (original + recording blend)
```

---

## 📊 CODE STRUCTURE

### MODEL Layer (Data Management)
- Audio file loading and caching
- Lyrics file parsing and timing generation
- Recording file saving
- Frequency analysis and correction
- Vocal onset detection

### VIEW Layer (User Interface)
- PyQt5 GUI components
- Real-time display updates
- Progress bar and time display
- Button controls and styling
- Transparent lyrics rendering

### CONTROLLER Layer (Application Logic)
- Event handling (button clicks)
- Playback control logic
- Recording management
- Audio mixing and resampling
- Synchronization timing

---

## 🚀 GETTING STARTED

### Running the Application
```bash
cd c:/Users/lbennicoff1/.vscode/YIN-Pitch/Pitch-Detection
python karaoke_gui.py
```

### Running Tests
```bash
python test_features.py
```

---

## 📝 KEY IMPLEMENTATION LOCATIONS

### Audio Frequency Analysis
- **File**: `karaoke_gui.py`
- **Class**: `AudioAnalyzer`
- **Method**: `analyze_frequency()` and `match_frequency()`
- **Line Range**: Approximately lines 25-85

### Lyrics Timing Generation
- **File**: `karaoke_gui.py`
- **Class**: `LyricsAnalyzer`
- **Method**: `generate_auto_timing()`
- **Line Range**: Approximately lines 105-120

### Recording & Playback
- **File**: `karaoke_gui.py`
- **Class**: `KaraokeController`
- **Methods**: `start_recording_with_playback()`, `playback_recording_with_original()`
- **Line Range**: Approximately lines 420-500

### Synchronization with Recording
- **File**: `karaoke_gui.py`
- **Class**: `KaraokeController`
- **Method**: `on_record_pressed()` triggers synchronized playback
- **Line Range**: Approximately line 420

---

## ✨ SPECIAL FEATURES

### Star Wars Opening Effect
The lyrics display creates a perspective effect:
- Large magenta current line
- Smaller, fading previous lines above
- Smaller, fading next lines below
- Smooth upward scrolling as song progresses

### Frequency Synchronization
Ensures recorded voice matches the original track frequency:
- Analyzes frequency profiles
- Calculates correction factor
- Auto-resamples if needed
- Plays mixed audio in correct sync

### Intelligent Timing
Automatically distributes lyrics if timestamps aren't provided:
- Evenly spaces lyrics across song duration
- Detects vocal onsets for better timing
- Supports manual timestamped format (MM:SS:Lyrics)

---

## 🧪 TEST RESULTS

All 7 feature tests passed:
✅ Audio Loading - 2,001,920 samples loaded successfully
✅ Lyrics Loading - 66 lyrics lines loaded with auto-timing
✅ Frequency Analysis - Dominant frequencies detected
✅ Lyrics Auto-Timing - Timestamps generated correctly
✅ Recording Features - Files saved and verified
✅ Frequency Correction - Correction factor calculated (0.952)
✅ Vocal Onset Detection - Working correctly

---

## 🎤 USAGE WORKFLOW

1. **Start Application**: Launches GUI with song loaded
2. **Play**: Click Play to start with synchronized lyrics
3. **Record**: Click Record to start singing along (plays song + records voice)
4. **Monitor**: Watch lyrics highlight and scroll as song plays
5. **Stop**: Click Stop to end playback
6. **Playback Recording**: Listen to your recording mixed with the original
7. **Frequency Analysis**: Automatic frequency correction applied

---

## 🔧 TECHNICAL SPECIFICATIONS

- **Framework**: PyQt5 (cross-platform GUI)
- **Audio Library**: sounddevice, soundfile (high-quality audio)
- **Signal Processing**: scipy, numpy (frequency analysis)
- **Python Version**: 3.13+
- **Sample Rate**: 48kHz (original), 44.1kHz (recording)
- **Audio Format**: WAV (lossless)
- **GUI Theme**: Dark mode with neon green (#00ff00) accents

---

## 📦 FILES INCLUDED

- **karaoke_gui.py** - Main application (750+ lines, fully documented)
- **test_features.py** - Comprehensive test suite
- **recording.wav** - Generated recording file

---

## ✅ VERIFICATION

The application has been:
- ✓ Built with proper MVC architecture
- ✓ Fully documented with comprehensive docstrings
- ✓ Tested multiple times for stability
- ✓ Feature-tested with dedicated test suite (7/7 passing)
- ✓ Debugged and optimized for performance

---

**Status**: ✅ COMPLETE AND TESTED
**Last Updated**: April 22, 2026
**Version**: 1.0.0 (Mister Microphone)
