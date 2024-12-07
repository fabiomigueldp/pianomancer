
# Pianomancer 🎹✨

Transform your keyboard into a magical piano with **Pianomancer**!  
A blend of music, visuals, and interactivity, Pianomancer allows you to create melodies, load MIDI files, and enjoy a captivating dynamic visualization.

---

![Pianomancer Preview](pianomancer.jpg)

---

## 🌟 Features

- 🎼 **Virtual Keyboard:** Play notes using your computer keyboard.
- 🎥 **Dynamic Visualization:** A beautiful Christmas tree reacts to your music in real-time.
- 🎹 **SoundFont Support:** Customize the instrument sound by selecting your preferred `.sf2` files.
- 🎶 **MIDI Playback:** Load and play MIDI files for an immersive experience.
- 🔴 **Record & Playback:** Record your melodies and listen to them anytime.
- 🔁 **Loop Playback Mode:** Automatically restart MIDI playback upon completion (toggle with `3` key).
- 🎛️ **Customizable Controls:** Adjust octave, playback speed, and more, even during playback.

---

## 🚀 Installation

### Prerequisites

- **Python 3.6+**  
  Download from [python.org](https://www.python.org/downloads/).

---

### 📦 Install on Linux

1. **Install FluidSynth**  
   ```bash
   sudo apt-get update
   sudo apt-get install fluidsynth
   ```

2. **Clone the Repository**  
   ```bash
   git clone https://github.com/fabiomigueldp/pianomancer.git
   cd pianomancer
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**  
   ```bash
   python pianomancer.py
   ```

---

### 🍎 Install on macOS

1. **Install Homebrew** (if not installed)  
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FluidSynth**  
   ```bash
   brew install fluid-synth
   ```

3. **Clone the Repository**  
   ```bash
   git clone https://github.com/fabiomigueldp/pianomancer.git
   cd pianomancer
   ```

4. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**  
   ```bash
   python pianomancer.py
   ```

---

### 🖥️ Install on Windows

1. **Download FluidSynth**  
   Download the latest release from [FluidSynth GitHub](https://github.com/FluidSynth/fluidsynth/releases).  
   Extract the files and add the FluidSynth executable to your system's PATH.

2. **Install `windows-curses`**  
   ```bash
   pip install windows-curses
   ```

3. **Clone the Repository**  
   ```bash
   git clone https://github.com/fabiomigueldp/pianomancer.git
   cd pianomancer
   ```

4. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**  
   ```bash
   python pianomancer.py
   ```

---

## 🎹 How to Use

1. **Launch the Application**  
   ```bash
   python pianomancer.py
   ```

2. **Controls:**

   - 🎵 Press keys to play notes (see the virtual keyboard).
   - 🔴 Press `R` to start/stop recording.
   - 🔊 Press `P` to playback your recording.
   - 🎼 Press `1` to load and play a MIDI file.
   - 🎨 Press `2` to change the SoundFont.
   - 🔁 Toggle Loop Playback: `3`.
   - ▶️ Play/Pause MIDI Playback: `4`.
   - 🔼 Adjust the octave: `[Decrease]` / `[Increase]`.
   - ⏩ Adjust playback speed: `-` / `+`.
   - ❌ Quit: `Q`.  
     Stop MIDI playback: `S`.

3. **Visual Feedback**  
   The Christmas tree lights up dynamically, reacting to your interactions, with active notes displayed below. During MIDI playback, the status (Playing/Paused) is displayed for better awareness.

---

## 📜 Changelog

### v1.2

- **Play/Pause MIDI Playback:**  
  Press `4` to toggle between playing and pausing the current MIDI playback, offering greater control over your listening experience.

- **Dynamic SoundFont Management:**  
  Ability to change the SoundFont (`2` key) during MIDI playback. The application will automatically pause playback, allow you to select a new SoundFont, and then resume playback seamlessly.

- **Enhanced Playback Controls:**  
  Adjust octave (`[`/`]`) and playback speed (`-`/`+`) even while a MIDI file is playing, providing more flexibility in how you experience your music.

- **MIDIPlayer Class Enhancements:**  
  Improved the MIDIPlayer class to handle new playback states such as pausing, resuming, and integrating SoundFont changes without interrupting the user experience.

- **Visual Feedback Improvements:**  
  Added MIDI playback status display (Playing/Paused) to keep users informed about the current state of MIDI playback.

- **Code Refactoring and Stability:**  
  Optimized event handling and error management to ensure smoother performance and prevent conflicts between different controls.

### v1.1

- **Loop Playback Mode:** Press `3` to toggle loop mode. When active, MIDI playback will automatically restart upon completion. The status is displayed as "Loop Mode: ON/OFF."
- **Enhanced Playback Controls:** Adjust playback speed (`-`/`+`) and octave (`[`/`]`) even during MIDI playback.
- Removed `[` from the virtual keyboard to resolve conflicts with octave decrease functionality.
- Removed `-` from the virtual keyboard to resolve conflicts with playback speed adjustment.

### v1.0

- Initial release of Pianomancer with dynamic visuals, MIDI playback, and SoundFont support.

---

## 🛠️ Development

### Contributing
Feel free to fork the repository and submit a pull request with your improvements!

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).  

---

## 👤 Author

**Fábio Miguel Denda Pacheco**  
*Created on December 4, 2024*  

---

### 🌐 Connect
- Discord: https://discord.gg/mx3aUF4C
