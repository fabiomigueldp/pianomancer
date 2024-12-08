import sys
import time
import os
import curses
import mido
import logging
import fluidsynth
import threading
import platform
import random

logging.basicConfig(
    filename='pianomancer.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

NOTE_MIDI_NUMBERS = {
    'z': 48,
    's': 49,
    'x': 50,
    'd': 51,
    'c': 52,
    'v': 53,
    'g': 54,
    'b': 55,
    'h': 56,
    'n': 57,
    'j': 58,
    'm': 59,
    ',': 60,
    'l': 61,
    '.': 62,
    ';': 63,
    '/': 64,
    'q': 65,
    'w': 67,
    'e': 69,
    'r': 71,
    't': 72,
    'y': 74,
    'u': 76,
    'i': 77,
    'o': 79,
    'p': 81,
    '=': 84,
}

class ChristmasTreeDisplay:
    def __init__(self, tree_lines, color_pairs, stdscr):
        self.tree_lines = tree_lines
        self.color_pairs = color_pairs
        self.stdscr = stdscr
        self.light_states = {}
        self.min_delay = 0.5
        self.max_delay = 2.0
        self.initialize_lights()
        self.active_notes = set()
        self.note_display_start_line = len(tree_lines) + 2

    def initialize_lights(self):
        current_time = time.time()
        for line_idx, line in enumerate(self.tree_lines):
            for char_idx, char in enumerate(line):
                if char == 'O':
                    color = random.choice(self.color_pairs)
                    next_change = current_time + random.uniform(self.min_delay, self.max_delay)
                    self.light_states[(line_idx, char_idx)] = {'color': color, 'next_change': next_change}

    def update_lights(self):
        current_time = time.time()
        for position, state in self.light_states.items():
            if current_time >= state['next_change']:
                available_colors = [cp for cp in self.color_pairs if cp != state['color']]
                if not available_colors:
                    available_colors = self.color_pairs
                new_color = random.choice(available_colors)
                self.light_states[position]['color'] = new_color
                self.light_states[position]['next_change'] = current_time + random.uniform(self.min_delay, self.max_delay)

    def draw_tree(self):
        max_y, max_x = self.stdscr.getmaxyx()
        try:
            for x in range(max_x):
                self.stdscr.addch(0, x, '-', curses.color_pair(4))
                self.stdscr.addch(max_y - 1, x, '-', curses.color_pair(4))
            for y in range(max_y):
                self.stdscr.addch(y, 0, '|', curses.color_pair(4))
                self.stdscr.addch(y, max_x - 1, '|', curses.color_pair(4))
            self.stdscr.addch(0, 0, '+', curses.color_pair(4))
            self.stdscr.addch(0, max_x - 1, '+', curses.color_pair(4))
            self.stdscr.addch(max_y - 1, 0, '+', curses.color_pair(4))
            self.stdscr.addch(max_y - 1, max_x - 1, '+', curses.color_pair(4))
        except curses.error:
            pass
        tree_width = max(len(line) for line in self.tree_lines)
        start_x = (max_x - tree_width) // 2
        for line_idx, line in enumerate(self.tree_lines):
            if line_idx + 1 >= max_y - 2:
                break
            for char_idx, char in enumerate(line):
                x_position = start_x + char_idx
                y_position = line_idx + 1
                if 0 <= x_position < max_x - 1 and 0 <= y_position < max_y - 1:
                    if char == '★':
                        self.stdscr.addstr(y_position, x_position, char, curses.color_pair(7) | curses.A_BOLD)
                    elif char == 'O':
                        if (line_idx, char_idx) in self.light_states:
                            color = self.light_states[(line_idx, char_idx)]['color']
                        else:
                            color = curses.color_pair(7)
                        self.stdscr.addstr(y_position, x_position, char, color)
                    elif char == '*':
                        self.stdscr.addstr(y_position, x_position, char, curses.color_pair(2))
                    else:
                        self.stdscr.addstr(y_position, x_position, char, curses.color_pair(7))
        self.stdscr.noutrefresh()

    def draw_active_notes(self):
        max_y, max_x = self.stdscr.getmaxyx()
        try:
            for x in range(1, max_x - 1):
                self.stdscr.addch(self.note_display_start_line, x, ' ', curses.color_pair(7))
        except curses.error:
            pass
        note_range = list(range(21, 109))
        max_note_val = max(note_range)
        max_display_x = max_x - 2
        num_notes = len(note_range)
        note_width = max_display_x // num_notes
        for idx, note in enumerate(note_range):
            column = 1 + idx * note_width + note_width // 2
            if note in self.active_notes:
                try:
                    self.stdscr.addstr(self.note_display_start_line, column, '█', curses.color_pair(random.choice([1, 2, 3, 5, 6])))
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addstr(self.note_display_start_line, column, ' ', curses.color_pair(7))
                except curses.error:
                    pass
        self.stdscr.noutrefresh()

    def update_display(self):
        self.update_lights()
        self.draw_tree()
        self.draw_active_notes()

def piano_app(stdscr):
    try:
        curses.curs_set(0)
        stdscr.nodelay(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_CYAN, -1)
        curses.init_pair(7, curses.COLOR_WHITE, -1)
        octave_shift = 0
        playback_speed = 1.0
        recording = []
        is_recording = False
        pressed_keys = {}
        key_to_midi_note = {}
        midi_mode = False
        midi_player = None
        loop_mode = False
        paused_for_soundfont = False
        operating_system = platform.system()
        logging.info(f"Detected operating system: {operating_system}")
        if operating_system == "Linux":
            driver = "alsa"
        elif operating_system == "Darwin":
            driver = "coreaudio"
        elif operating_system == "Windows":
            driver = "dsound"
        else:
            driver = "alsa"
        logging.info(f"Trying to start FluidSynth with driver: {driver}")
        fs = fluidsynth.Synth()
        try:
            fs.start(driver=driver)
            logging.info(f"FluidSynth started successfully using driver '{driver}'.")
        except Exception as e:
            logging.error(f"Failed to start FluidSynth with driver '{driver}': {e}")
            if driver != "alsa":
                try:
                    alternative_driver = "alsa"
                    fs.start(driver=alternative_driver)
                    logging.info(f"FluidSynth started successfully using alternative driver '{alternative_driver}'.")
                    driver = alternative_driver
                except Exception as ex:
                    logging.exception("Failed to start FluidSynth with available drivers.")
                    stdscr.addstr(0, 0, "Error starting FluidSynth. Check the log for details.")
                    stdscr.refresh()
                    time.sleep(2)
                    return
            else:
                logging.exception("No audio driver available for FluidSynth.")
                stdscr.addstr(0, 0, "No audio driver available for FluidSynth. Check the log for details.")
                stdscr.refresh()
                time.sleep(2)
                return
        soundfonts = [f for f in os.listdir('.') if f.lower().endswith('.sf2')]
        if not soundfonts:
            logging.error("No SoundFont (.sf2) files found in the current directory.")
            stdscr.addstr(0, 0, "No SoundFont (.sf2) files found in the current directory.")
            stdscr.refresh()
            time.sleep(2)
            return
        selected_soundfont = select_soundfont(stdscr, soundfonts)
        stdscr.clear()
        if not selected_soundfont:
            logging.info("SoundFont selection canceled by user.")
            return
        try:
            soundfont_id = fs.sfload(selected_soundfont)
            fs.program_select(0, soundfont_id, 0, 0)
            logging.info(f"SoundFont '{selected_soundfont}' loaded successfully.")
        except Exception as e:
            logging.exception(f"Error loading SoundFont '{selected_soundfont}'.")
            stdscr.addstr(0, 0, f"Error loading SoundFont '{selected_soundfont}'. Check the log.")
            stdscr.refresh()
            time.sleep(2)
            return
        midi_files = [f for f in os.listdir('.') if f.lower().endswith(('.mid', '.midi'))]
        selected_midi = None
        instructions = [
            "Pianomancer - Transform your keyboard into a piano!",
            "",
            "Instructions:",
            "Press the keys to play notes (see the virtual keyboard below).",
            "'R' to start/stop recording, 'P' to play recording.",
            "'1' to enter MIDI playback mode.",
            "'2' to change the SoundFont (during playback pauses and resumes).",
            "'3' to toggle loop mode ON/OFF.",
            "'4' to play/pause current MIDI playback.",
            "'[' or ']' to decrease/increase the octave.",
            "'-' or '+' to decrease/increase playback speed.",
            "'Q' to quit, 'S' to stop MIDI playback.",
            "",
            "Virtual Keyboard:"
        ]
        tree_lines = [
            "        ★        ",
            "        *        ",
            "       ***       ",
            "      *O*O*      ",
            "     *******     ",
            "    *O*****O*    ",
            "   ***********   ",
            "  *O*********O*  ",
            "       ***       ",
            "       ***       "
        ]
        tree_display = ChristmasTreeDisplay(
            tree_lines=tree_lines,
            color_pairs=[curses.color_pair(1), curses.color_pair(2),
                         curses.color_pair(3), curses.color_pair(5),
                         curses.color_pair(6)],
            stdscr=stdscr
        )
        virtual_keyboard = ' '.join(NOTE_MIDI_NUMBERS.keys())
        active_notes = set()
        def apply_octave_shift(new_shift):
            nonlocal octave_shift, midi_player, active_notes
            old_shift = octave_shift
            octave_shift = new_shift
            logging.info(f"Octave changed from {old_shift} to {octave_shift}. Re-triggering notes if necessary.")
            for midi_note in list(active_notes):
                fs.noteoff(0, midi_note)
                active_notes.remove(midi_note)
            if midi_mode and midi_player:
                midi_player.set_octave_shift(octave_shift)
        def apply_playback_speed(new_speed):
            nonlocal playback_speed, midi_player
            old_speed = playback_speed
            playback_speed = new_speed
            logging.info(f"Playback speed changed from {old_speed:.1f}x to {playback_speed:.1f}x.")
            if midi_mode and midi_player:
                midi_player.set_playback_speed(playback_speed)
        while True:
            try:
                max_y, max_x = stdscr.getmaxyx()
                for y in range(tree_display.note_display_start_line + 1, max_y):
                    stdscr.move(y, 0)
                    stdscr.clrtoeol()
                tree_display.active_notes = active_notes
                tree_display.update_display()
                start_line = tree_display.note_display_start_line + 2
                for idx, line in enumerate(instructions):
                    stdscr.addstr(start_line + idx, 2, line, curses.color_pair(7))
                stdscr.addstr(start_line + len(instructions), 2, virtual_keyboard, curses.color_pair(3))
                stdscr.addstr(start_line + len(instructions) + 1, 2, f"Octave Shift: {octave_shift}", curses.color_pair(6))
                stdscr.addstr(start_line + len(instructions) + 2, 2, f"Playback Speed: {playback_speed:.1f}x", curses.color_pair(6))
                loop_status = "ON" if loop_mode else "OFF"
                stdscr.addstr(start_line + len(instructions) + 3, 2, f"Loop Mode: {loop_status}", curses.color_pair(6))
                if is_recording:
                    stdscr.addstr(start_line + len(instructions) + 4, 2, "Recording... (Press 'R' to stop)", curses.color_pair(1))
                if midi_mode and midi_player:
                    pause_status = "Paused" if midi_player.paused else "Playing"
                    stdscr.addstr(start_line + len(instructions) + 5, 2, f"MIDI Status: {pause_status}", curses.color_pair(6))
                stdscr.noutrefresh()
                curses.doupdate()
                try:
                    key = stdscr.getch()
                except curses.error:
                    key = -1
                current_time = time.perf_counter()
                if key != -1:
                    try:
                        key_char = chr(key).lower()
                    except ValueError:
                        key_char = ''
                    logging.debug(f"Key pressed: {key_char}")
                    if key_char == 'q':
                        if midi_mode and midi_player:
                            midi_player.stop()
                            midi_mode = False
                            logging.info("MIDI playback interrupted by user.")
                        else:
                            logging.info("Exiting application by user.")
                            break
                    elif key_char == 's':
                        if midi_mode and midi_player:
                            midi_player.stop()
                            midi_mode = False
                            logging.info("MIDI playback stopped by user.")
                    elif key_char == '[':
                        apply_octave_shift(octave_shift - 1)
                    elif key_char == ']':
                        apply_octave_shift(octave_shift + 1)
                    elif key_char == '-':
                        new_speed = max(0.1, playback_speed - 0.1)
                        apply_playback_speed(new_speed)
                    elif key_char == '+':
                        new_speed = playback_speed + 0.1
                        apply_playback_speed(new_speed)
                    elif key_char == '3':
                        loop_mode = not loop_mode
                        if midi_mode and midi_player:
                            midi_player.loop_mode = loop_mode
                        logging.info(f"Loop mode toggled: {loop_mode}")
                    elif key_char == '4':
                        if midi_mode and midi_player:
                            midi_player.toggle_pause()
                            logging.info(f"Play/Pause toggled. Now paused={midi_player.paused}")
                    else:
                        if not midi_mode:
                            if key_char in NOTE_MIDI_NUMBERS:
                                midi_note = NOTE_MIDI_NUMBERS[key_char] + (octave_shift * 12)
                                if key_char not in key_to_midi_note:
                                    fs.noteon(0, midi_note, 127)
                                    active_notes.add(midi_note)
                                    key_to_midi_note[key_char] = midi_note
                                    logging.debug(f"Playing note: {key_char} (MIDI {midi_note})")
                                pressed_keys[key_char] = current_time
                                if is_recording:
                                    recording.append(('note_on', midi_note, current_time))
                                    logging.debug(f"Recording note ON: {key_char} at {current_time}")
                            elif key_char == 'r':
                                if not is_recording:
                                    recording = []
                                    is_recording = True
                                    logging.info("Recording started.")
                                else:
                                    is_recording = False
                                    for midi_note in list(active_notes):
                                        recording.append(('note_off', midi_note, current_time))
                                        fs.noteoff(0, midi_note)
                                        active_notes.remove(midi_note)
                                    key_to_midi_note.clear()
                                    logging.info("Recording stopped.")
                            elif key_char == 'p':
                                if recording:
                                    is_recording = False
                                    play_recording(recording, octave_shift, playback_speed, fs, stdscr)
                                else:
                                    stdscr.addstr(start_line + len(instructions) + 6, 2, "No recording to play.", curses.color_pair(1))
                                    stdscr.refresh()
                                    time.sleep(1)
                                    logging.info("Attempted playback without recording.")
                            elif key_char == '1':
                                if midi_files:
                                    selected_midi = select_midi_file(stdscr, midi_files)
                                    stdscr.clear()
                                    if selected_midi:
                                        midi_mode = True
                                        midi_player = MIDIPlayer(selected_midi, octave_shift, playback_speed, fs, active_notes, stdscr, loop_mode)
                                        logging.info(f"Starting MIDI playback: {selected_midi}")
                                else:
                                    stdscr.addstr(start_line + len(instructions) + 6, 2, "No MIDI files found.", curses.color_pair(1))
                                    stdscr.refresh()
                                    time.sleep(1)
                                    logging.info("No MIDI files found for playback.")
                            elif key_char == '2':
                                soundfonts = [f for f in os.listdir('.') if f.lower().endswith('.sf2')]
                                if not soundfonts:
                                    logging.error("No SoundFont (.sf2) files found in the current directory.")
                                    stdscr.addstr(0, 0, "No SoundFont (.sf2) files found.")
                                    stdscr.refresh()
                                    time.sleep(2)
                                    continue
                                new_sf = select_soundfont(stdscr, soundfonts)
                                stdscr.clear()
                                if new_sf:
                                    try:
                                        soundfont_id = fs.sfload(new_sf)
                                        for channel in range(16):
                                            fs.program_select(channel, soundfont_id, 0, 0)
                                        logging.info(f"SoundFont '{new_sf}' loaded successfully.")
                                    except Exception as e:
                                        logging.exception(f"Error loading SoundFont '{new_sf}'.")
                                        stdscr.addstr(0, 0, f"Error loading SoundFont '{new_sf}'. Check the log.")
                                        stdscr.refresh()
                                        time.sleep(2)
                                else:
                                    logging.info("SoundFont selection canceled by user.")
                            elif key_char == ' ':
                                for midi_note in list(active_notes):
                                    if is_recording:
                                        recording.append(('note_off', midi_note, current_time))
                                    fs.noteoff(0, midi_note)
                                    active_notes.remove(midi_note)
                                key_to_midi_note.clear()
                                logging.debug("All notes stopped manually.")
                        else:
                            if key_char == '2':
                                if midi_player:
                                    midi_player.pause_for_soundfont_change()
                                soundfonts = [f for f in os.listdir('.') if f.lower().endswith('.sf2')]
                                if not soundfonts:
                                    logging.error("No SoundFont (.sf2) files found in the directory.")
                                    stdscr.addstr(0, 0, "No SoundFont (.sf2) files found.")
                                    stdscr.refresh()
                                    time.sleep(2)
                                    if midi_player:
                                        midi_player.resume_after_soundfont_change()
                                    continue
                                new_sf = select_soundfont(stdscr, soundfonts)
                                stdscr.clear()
                                if new_sf:
                                    try:
                                        soundfont_id = fs.sfload(new_sf)
                                        for channel in range(16):
                                            fs.program_select(channel, soundfont_id, 0, 0)
                                        logging.info(f"SoundFont '{new_sf}' loaded during playback successfully.")
                                        midi_player.resume_after_soundfont_change()
                                    except Exception as e:
                                        logging.exception(f"Error loading SoundFont '{new_sf}'.")
                                        stdscr.addstr(0, 0, f"Error loading SoundFont '{new_sf}'. Check the log.")
                                        stdscr.refresh()
                                        time.sleep(2)
                                        midi_player.resume_after_soundfont_change()
                                else:
                                    logging.info("SoundFont selection canceled by user.")
                                    if midi_player:
                                        midi_player.resume_after_soundfont_change()
                if midi_mode and midi_player:
                    if not midi_player.is_playing:
                        if midi_player.loop_mode:
                            pass
                        else:
                            midi_mode = False
                            logging.info("MIDI playback mode deactivated.")
                    else:
                        midi_player.update()
                keys_to_stop = []
                for k_char, t in pressed_keys.items():
                    if current_time - t > 0.1:
                        keys_to_stop.append(k_char)
                for k_char in keys_to_stop:
                    if k_char in key_to_midi_note:
                        midi_note = key_to_midi_note[k_char]
                        if is_recording:
                            recording.append(('note_off', midi_note, current_time))
                        fs.noteoff(0, midi_note)
                        if midi_note in active_notes:
                            active_notes.remove(midi_note)
                        del key_to_midi_note[k_char]
                        logging.debug(f"Recording note OFF after threshold: {k_char} at {current_time}")
                    del pressed_keys[k_char]
                time.sleep(0.01)
            except Exception as e:
                logging.exception("Error in piano_app function.")
                raise e
    except Exception as e:
        logging.exception("Error in piano_app function.")
        raise e
    finally:
        curses.endwin()
        fs.delete()
        logging.info("Application exited and curses terminated.")

def play_recording(recording, octave_shift, playback_speed, fs, stdscr):
    try:
        if not recording:
            logging.info("No recording to play.")
            return
        start_time = recording[0][2]
        active_notes = set()
        ref_start = time.perf_counter()
        last_event_time = start_time
        for i, event in enumerate(recording):
            event_type, midi_note, event_time = event
            wait_time = (event_time - last_event_time) / playback_speed
            if wait_time > 0:
                time.sleep(wait_time)
            last_event_time = event_time
            adjusted_note = midi_note + (octave_shift * 12)
            if event_type == 'note_on':
                fs.noteon(0, adjusted_note, 127)
                active_notes.add(adjusted_note)
                logging.debug(f"Playing note ON: MIDI {adjusted_note}")
            elif event_type == 'note_off':
                fs.noteoff(0, adjusted_note)
                if adjusted_note in active_notes:
                    active_notes.remove(adjusted_note)
                logging.debug(f"Playing note OFF: MIDI {adjusted_note}")
        for note in active_notes:
            fs.noteoff(0, note)
        logging.info("Recording playback completed.")
    except Exception as e:
        logging.exception("Error during playback.")

class MIDIPlayer:
    def __init__(self, midi_file, octave_shift, playback_speed, fs, global_active_notes, stdscr, loop_mode=False):
        try:
            self.midi = mido.MidiFile(midi_file)
            self.octave_shift = octave_shift
            self.playback_speed = playback_speed
            self.fs = fs
            self.is_playing = True
            self.interrupted = False
            self.active_notes = set()
            self.global_active_notes = global_active_notes
            self.loop_mode = loop_mode
            self.stdscr = stdscr
            self.paused = False
            self.paused_for_soundfont = False
            self.prepare_messages()
            logging.info(f"MIDIPlayer initialized for file: {midi_file}")
        except Exception as e:
            logging.exception("Error initializing MIDIPlayer.")

    def prepare_messages(self):
        try:
            self.message_queue = []
            absolute_time = 0
            for msg in self.midi:
                time_in_seconds = msg.time
                absolute_time += time_in_seconds
                self.message_queue.append((absolute_time, msg))
            self.message_queue.sort(key=lambda x: x[0])
            self.total_messages = len(self.message_queue)
            self.current_message_index = 0
            self.start_time = time.perf_counter()
            self.base_logical_time = 0.0
            self.pause_offset = 0.0
            logging.info("MIDI messages prepared for playback.")
        except Exception as e:
            logging.exception("Error preparing MIDI messages.")

    def update(self):
        if self.interrupted or not self.is_playing or self.paused or self.paused_for_soundfont:
            return
        try:
            current_logical_time = ((time.perf_counter() - self.start_time) * self.playback_speed) - self.pause_offset
            while self.current_message_index < self.total_messages:
                message_time, msg = self.message_queue[self.current_message_index]
                if current_logical_time >= message_time:
                    if not msg.is_meta:
                        channel = msg.channel if hasattr(msg, 'channel') else 0
                        if msg.type == 'note_on' and msg.velocity > 0:
                            midi_note = msg.note + (self.octave_shift * 12)
                            self.fs.noteon(channel, midi_note, msg.velocity)
                            self.active_notes.add((channel, msg.note))
                            self.global_active_notes.add(midi_note)
                            logging.debug(f"Note ON: Ch {channel} MIDI {midi_note} Velocity {msg.velocity}")
                        elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                            midi_note = msg.note + (self.octave_shift * 12)
                            self.fs.noteoff(channel, midi_note)
                            if (channel, msg.note) in self.active_notes:
                                self.active_notes.remove((channel, msg.note))
                            if midi_note in self.global_active_notes:
                                self.global_active_notes.remove(midi_note)
                            logging.debug(f"Note OFF: Ch {channel} MIDI {midi_note}")
                        elif msg.type == 'program_change':
                            self.fs.program_change(channel, msg.program)
                            logging.debug(f"Program Change: Ch {channel} Program {msg.program}")
                    self.current_message_index += 1
                else:
                    break
            if self.current_message_index >= self.total_messages and not self.active_notes:
                if self.loop_mode and not self.interrupted:
                    self.current_message_index = 0
                    self.start_time = time.perf_counter()
                    self.pause_offset = 0.0
                    logging.info("MIDI playback looped back to start.")
                else:
                    self.is_playing = False
                    logging.info("MIDI playback completed.")
        except Exception as e:
            logging.exception("Error during MIDIPlayer update.")

    def stop(self):
        for note_info in list(self.active_notes):
            channel, orig_note = note_info
            adjusted_note = orig_note + (self.octave_shift * 12)
            self.fs.noteoff(channel, adjusted_note)
            self.active_notes.remove(note_info)
            if adjusted_note in self.global_active_notes:
                self.global_active_notes.remove(adjusted_note)
        self.is_playing = False
        self.interrupted = True
        logging.info("MIDI playback stopped.")

    def set_octave_shift(self, new_shift):
        old_shift = self.octave_shift
        self.octave_shift = new_shift
        logging.info(f"Octave shift changed during playback from {old_shift} to {self.octave_shift}.")
        for note_info in list(self.active_notes):
            channel, orig_note = note_info
            old_midi = orig_note + (old_shift * 12)
            self.fs.noteoff(channel, old_midi)
            if old_midi in self.global_active_notes:
                self.global_active_notes.remove(old_midi)
            self.active_notes.remove(note_info)
        logging.info("Active notes stopped due to octave shift. Not re-triggering to avoid ambiguity.")

    def set_playback_speed(self, new_speed):
        old_speed = self.playback_speed
        current_real_time = time.perf_counter()
        current_logical_time = (current_real_time - self.start_time) * old_speed - self.pause_offset
        self.start_time = current_real_time - ((current_logical_time + self.pause_offset) / new_speed)
        self.playback_speed = new_speed
        logging.info(f"Playback speed updated from {old_speed}x to {new_speed}x during playback.")

    def toggle_pause(self):
        if self.paused:
            current_real_time = time.perf_counter()
            paused_duration = current_real_time - self.pause_start
            self.pause_offset += paused_duration * self.playback_speed
            self.paused = False
            logging.info("MIDI playback resumed.")
        else:
            for (channel, note) in list(self.active_notes):
                adjusted_note = note + (self.octave_shift * 12)
                self.fs.noteoff(channel, adjusted_note)
                self.global_active_notes.discard(adjusted_note)
                self.active_notes.remove((channel, note))
            self.paused = True
            self.pause_start = time.perf_counter()
            logging.info("MIDI playback paused.")

    def pause_for_soundfont_change(self):
        if not self.paused_for_soundfont:
            self.paused_for_soundfont = True
            self.sf_pause_start = time.perf_counter()
            for (channel, note) in list(self.active_notes):
                adjusted_note = note + (self.octave_shift * 12)
                self.fs.noteoff(channel, adjusted_note)
                self.global_active_notes.discard(adjusted_note)
                self.active_notes.remove((channel, note))
            logging.info("MIDI playback paused for SoundFont change.")

    def resume_after_soundfont_change(self):
        if self.paused_for_soundfont:
            current_real_time = time.perf_counter()
            paused_duration = current_real_time - self.sf_pause_start
            self.pause_offset += paused_duration * self.playback_speed
            self.paused_for_soundfont = False
            logging.info("MIDI playback resumed after SoundFont change.")

def select_midi_file(stdscr, midi_files):
    try:
        selected = 0
        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            title = "Select a MIDI file to play:"
            stdscr.addstr(1, max(0, (max_x - len(title)) // 2), title, curses.color_pair(6))
            for idx, file in enumerate(midi_files):
                if idx == selected:
                    stdscr.addstr(idx + 3, 2, f"> {file}", curses.color_pair(2) | curses.A_REVERSE)
                else:
                    stdscr.addstr(idx + 3, 2, f"  {file}", curses.color_pair(7))
            stdscr.addstr(len(midi_files) + 4, 2, "Use the up/down arrows to navigate and Enter to select. 'Q' to cancel.", curses.color_pair(6))
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(midi_files)
                logging.debug(f"Navigating up: {selected}")
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(midi_files)
                logging.debug(f"Navigating down: {selected}")
            elif key in [10, 13]:
                logging.info(f"Selected MIDI file: {midi_files[selected]}")
                return midi_files[selected]
            elif key in [ord('q'), ord('Q')]:
                logging.info("MIDI file selection canceled by user.")
                return None
    except Exception as e:
        logging.exception("Error in MIDI file selection.")
        return None

def select_soundfont(stdscr, soundfonts):
    try:
        selected = 0
        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            title = "Select a SoundFont (.sf2) to use:"
            stdscr.addstr(1, max(0, (max_x - len(title)) // 2), title, curses.color_pair(6))
            for idx, file in enumerate(soundfonts):
                if idx == selected:
                    stdscr.addstr(idx + 3, 2, f"> {file}", curses.color_pair(2) | curses.A_REVERSE)
                else:
                    stdscr.addstr(idx + 3, 2, f"  {file}", curses.color_pair(7))
            stdscr.addstr(len(soundfonts) + 4, 2, "Use the up/down arrows to navigate and Enter to select. 'Q' to cancel.", curses.color_pair(6))
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(soundfonts)
                logging.debug(f"Navigating up: {selected}")
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(soundfonts)
                logging.debug(f"Navigating down: {selected}")
            elif key in [10, 13]:
                logging.info(f"Selected SoundFont: {soundfonts[selected]}")
                return soundfonts[selected]
            elif key in [ord('q'), ord('Q')]:
                logging.info("SoundFont selection canceled by user.")
                return None
    except Exception as e:
        logging.exception("Error in SoundFont selection.")
        return None

if __name__ == "__main__":
    try:
        curses.wrapper(piano_app)
    except Exception as e:
        logging.exception("Error in main application execution.")
        print("An error occurred. Check the pianomancer.log file for more details.")

